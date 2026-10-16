from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Exists, OuterRef, Subquery
from django.utils import timezone

from core.common.profiles import profile_display_name
from hr_app.models import (
    Employee,
    OnboardingCard,
    OnboardingColumn,
    OnboardingEmployeeLink,
    OnboardingStageChange,
    Position,
)


class OnboardingNotFound(Exception):
    pass


class StaleOnboardingMove(Exception):
    pass


class OnboardingLinkConflict(Exception):
    pass


def _positive_id(value, field):
    if isinstance(value, bool):
        raise ValidationError({field: "Enter a valid ID."})
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError({field: "Enter a valid ID."})
    if parsed <= 0:
        raise ValidationError({field: "Enter a valid ID."})
    return parsed


def _label(value):
    label = str(value or "").strip()
    if not label or len(label) > 80:
        raise ValidationError({"label": "Enter a column label of up to 80 characters."})
    return label


def _position(value, maximum):
    if isinstance(value, bool):
        raise ValidationError({"position": "Enter a valid column position."})
    try:
        position = int(value)
    except (TypeError, ValueError):
        raise ValidationError({"position": "Enter a valid column position."})
    if position < 0 or position > maximum:
        raise ValidationError({"position": f"Column position must be between 0 and {maximum}."})
    return position


def column_payload(column, *, count=None):
    payload = {
        "id": column.id,
        "label": column.label,
        "phase": column.phase,
        "position": column.position,
        "is_active": column.is_active,
    }
    if count is not None:
        payload["count"] = count
    return payload


def card_payload(card):
    position = card.position
    has_employee_link = getattr(card, "has_employee_link", None)
    if has_employee_link is None:
        has_employee_link = bool(card.employee_id) or OnboardingEmployeeLink.objects.filter(card_id=card.id).exists()
    return {
        "id": card.id,
        "name": card.name,
        "email": card.email,
        "kind": card.column.phase,
        "column_id": card.column_id,
        "position": {"id": position.id, "title": position.title} if position else None,
        "employee_id": card.employee_id,
        "has_employee_link": has_employee_link,
        "notes": card.notes,
        "created_at": card.created_at.isoformat(),
        "updated_at": card.updated_at.isoformat(),
        "last_moved_at": card.last_moved_at.isoformat() if getattr(card, "last_moved_at", None) else None,
    }


def board_payload():
    columns = list(OnboardingColumn.objects.filter(is_active=True).order_by("phase", "position", "id"))
    archived_columns = list(OnboardingColumn.objects.filter(is_active=False).order_by("phase", "position", "id"))
    latest_move = (
        OnboardingStageChange.objects.filter(card_id=OuterRef("pk"), from_column__isnull=False)
        .order_by("-created_at", "-id")
        .values("created_at")[:1]
    )
    employee_link = OnboardingEmployeeLink.objects.filter(card_id=OuterRef("pk"))
    cards = list(
        OnboardingCard.objects.select_related("column", "position")
        .filter(column__is_active=True)
        .annotate(last_moved_at=Subquery(latest_move), has_employee_link=Exists(employee_link))
        .order_by("column__phase", "column__position", "-updated_at", "-id")
    )
    counts = {column.id: 0 for column in columns}
    for card in cards:
        counts[card.column_id] += 1
    return {
        "columns": [column_payload(column, count=counts[column.id]) for column in columns],
        "archived_columns": [column_payload(column) for column in archived_columns],
        "cards": [card_payload(card) for card in cards],
        "can_manage": True,
    }


def _reorder_columns(phase, moving_id, position):
    columns = list(
        OnboardingColumn.objects.select_for_update()
        .filter(phase=phase, is_active=True)
        .order_by("position", "id")
    )
    moving = next(column for column in columns if column.id == moving_id)
    columns.remove(moving)
    columns.insert(position, moving)
    for index, column in enumerate(columns):
        if column.position != index:
            OnboardingColumn.objects.filter(pk=column.pk).update(position=index, updated_at=timezone.now())
            column.position = index


@transaction.atomic
def create_column(data):
    phase = str(data.get("phase") or "").strip()
    if phase not in dict(OnboardingColumn.PHASE_CHOICES):
        raise ValidationError({"phase": "Choose applicant or onboarding."})
    label = _label(data.get("label"))
    existing = list(OnboardingColumn.objects.select_for_update().filter(phase=phase, is_active=True))
    if any(column.label.casefold() == label.casefold() for column in existing):
        raise ValidationError({"label": "This phase already has a column with that label."})
    position = _position(data.get("position"), len(existing)) if data.get("position") is not None else len(existing)
    column = OnboardingColumn.objects.create(label=label, phase=phase, position=len(existing))
    _reorder_columns(phase, column.id, position)
    column.refresh_from_db()
    return column


@transaction.atomic
def update_column(column_id, data):
    column = OnboardingColumn.objects.select_for_update().filter(pk=column_id).first()
    if column is None:
        raise OnboardingNotFound
    if not any(key in data for key in ("label", "position", "is_active")):
        raise ValidationError({"detail": "Provide a column field to update."})
    if "phase" in data:
        raise ValidationError({"phase": "A column's phase cannot be changed."})
    if "label" in data:
        label = _label(data.get("label"))
        if OnboardingColumn.objects.filter(phase=column.phase, is_active=True, label__iexact=label).exclude(pk=column.pk).exists():
            raise ValidationError({"label": "This phase already has a column with that label."})
        column.label = label
    if "is_active" in data:
        active = data.get("is_active")
        if not isinstance(active, bool):
            raise ValidationError({"is_active": "Enter true or false."})
        if active and not column.is_active and OnboardingColumn.objects.filter(
            phase=column.phase, is_active=True, label__iexact=column.label
        ).exclude(pk=column.pk).exists():
            raise ValidationError({"label": "This phase already has a column with that label."})
        if not active and column.is_active:
            if column.cards.exists():
                raise ValidationError({"is_active": "Move cards out of this column before archiving it."})
            if not OnboardingColumn.objects.filter(phase=column.phase, is_active=True).exclude(pk=column.pk).exists():
                raise ValidationError({"is_active": "Keep at least one active column in each phase."})
        if active and not column.is_active:
            column.position = OnboardingColumn.objects.filter(phase=column.phase, is_active=True).count()
        column.is_active = active
    column.save(update_fields=["label", "is_active", "position", "updated_at"])
    if column.is_active and "position" in data:
        count = OnboardingColumn.objects.filter(phase=column.phase, is_active=True).count()
        _reorder_columns(column.phase, column.id, _position(data.get("position"), count - 1))
    elif not column.is_active and "position" in data:
        raise ValidationError({"position": "Archived columns cannot be reordered."})
    elif not column.is_active:
        remaining = list(
            OnboardingColumn.objects.select_for_update()
            .filter(phase=column.phase, is_active=True)
            .order_by("position", "id")
        )
        for index, item in enumerate(remaining):
            if item.position != index:
                OnboardingColumn.objects.filter(pk=item.pk).update(position=index, updated_at=timezone.now())
    column.refresh_from_db()
    return column


@transaction.atomic
def create_card(*, actor, data):
    employee = None
    if data.get("employee_id") not in (None, ""):
        employee_id = _positive_id(data.get("employee_id"), "employee_id")
        employee = (
            Employee.objects.select_related("profile__user", "position")
            .select_for_update(of=("self",))
            .filter(pk=employee_id)
            .first()
        )
        if employee is None:
            raise ValidationError({"employee_id": "Employee record was not found."})
        if OnboardingCard.objects.filter(employee=employee).exists():
            raise ValidationError({"employee_id": "This employee already has an onboarding card."})
    name = str(data.get("name") or "").strip()
    if employee and not name:
        name = profile_display_name(employee.profile)
    if not name or len(name) > 160:
        raise ValidationError({"name": "Enter a name of up to 160 characters."})
    email = str(data.get("email") or (employee.profile.user.email if employee else "")).strip()
    if email:
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError({"email": "Enter a valid email address."})
    if len(email) > 254:
        raise ValidationError({"email": "Email must be 254 characters or fewer."})
    position = employee.position if employee else None
    if data.get("position_id") not in (None, ""):
        position_id = _positive_id(data.get("position_id"), "position_id")
        position = Position.objects.filter(pk=position_id, is_active=True).first()
        if position is None:
            raise ValidationError({"position_id": "Select an active position."})
    notes = str(data.get("notes") or "").strip()
    if len(notes) > 5000:
        raise ValidationError({"notes": "Notes must be 5000 characters or fewer."})
    if data.get("column_id") not in (None, ""):
        column_id = _positive_id(data.get("column_id"), "column_id")
        column = OnboardingColumn.objects.select_for_update().filter(pk=column_id, is_active=True).first()
    else:
        phase = OnboardingColumn.PHASE_ONBOARDING if employee else OnboardingColumn.PHASE_APPLICANT
        column = (
            OnboardingColumn.objects.select_for_update()
            .filter(phase=phase, is_active=True)
            .order_by("position", "id")
            .first()
        )
    if column is None:
        raise ValidationError({"column_id": "Select an active board column."})
    if employee and column.phase != OnboardingColumn.PHASE_ONBOARDING:
        raise ValidationError({"column_id": "Existing employees must start in an onboarding column."})
    card = OnboardingCard.objects.create(
        name=name,
        email=email,
        position=position,
        employee=employee,
        column=column,
        notes=notes,
        created_by=actor,
        updated_by=actor,
    )
    OnboardingStageChange.objects.create(
        card=card,
        to_column=column,
        to_label=column.label,
        to_phase=column.phase,
        actor=actor,
        actor_name=profile_display_name(actor),
        reason="Card created.",
    )
    if employee:
        OnboardingEmployeeLink.objects.create(
            card=card,
            employee=employee,
            employee_no=employee.employee_no,
            employee_name=profile_display_name(employee.profile),
            actor=actor,
            actor_name=profile_display_name(actor),
        )
    card.has_employee_link = bool(employee)
    card.last_moved_at = None
    return card


@transaction.atomic
def move_card(*, actor, card_id, data):
    expected_column_id = _positive_id(data.get("expected_column_id"), "expected_column_id")
    destination_id = _positive_id(data.get("column_id"), "column_id")
    card = (
        OnboardingCard.objects.select_related("column", "position")
        .select_for_update(of=("self",))
        .filter(pk=card_id)
        .first()
    )
    if card is None:
        raise OnboardingNotFound
    if card.column_id != expected_column_id:
        raise StaleOnboardingMove
    if destination_id == card.column_id:
        raise ValidationError({"column_id": "Card is already in that column."})
    destination = OnboardingColumn.objects.select_for_update().filter(pk=destination_id, is_active=True).first()
    if destination is None:
        raise ValidationError({"column_id": "Select an active board column."})
    if (card.employee_id or OnboardingEmployeeLink.objects.filter(card_id=card.id).exists()) and destination.phase != OnboardingColumn.PHASE_ONBOARDING:
        raise ValidationError({"column_id": "An employee card must stay in onboarding columns."})
    reason = str(data.get("reason") or "").strip()
    if len(reason) > 1000:
        raise ValidationError({"reason": "Reason must be 1000 characters or fewer."})
    source = card.column
    changed_at = timezone.now()
    updated = OnboardingCard.objects.filter(pk=card.pk, column_id=expected_column_id).update(
        column=destination,
        updated_by=actor,
        updated_at=changed_at,
    )
    if updated != 1:
        raise StaleOnboardingMove
    change = OnboardingStageChange.objects.create(
        card=card,
        from_column=source,
        from_label=source.label,
        from_phase=source.phase,
        to_column=destination,
        to_label=destination.label,
        to_phase=destination.phase,
        actor=actor,
        actor_name=profile_display_name(actor),
        reason=reason,
    )
    card.column = destination
    card.updated_at = changed_at
    card.last_moved_at = change.created_at
    return card


@transaction.atomic
def link_employee(*, actor, card_id, data):
    employee_id = _positive_id(data.get("employee_id"), "employee_id")
    expected_column_id = _positive_id(data.get("expected_column_id"), "expected_column_id")
    card = (
        OnboardingCard.objects.select_related("column", "position")
        .select_for_update(of=("self",))
        .filter(pk=card_id)
        .first()
    )
    if card is None:
        raise OnboardingNotFound
    if card.column_id != expected_column_id:
        raise StaleOnboardingMove
    if card.column.phase != OnboardingColumn.PHASE_ONBOARDING:
        raise ValidationError({"column_id": "Move the card to an onboarding column before linking an employee."})
    if card.employee_id or OnboardingEmployeeLink.objects.filter(card_id=card.id).exists():
        raise OnboardingLinkConflict

    employee = (
        Employee.objects.select_related("profile__user", "position")
        .select_for_update(of=("self",))
        .filter(pk=employee_id)
        .first()
    )
    if employee is None:
        raise ValidationError({"employee_id": "Employee record was not found."})
    if OnboardingCard.objects.filter(employee_id=employee.id).exists():
        raise OnboardingLinkConflict

    linked_at = timezone.now()
    updated = OnboardingCard.objects.filter(
        pk=card.pk,
        column_id=expected_column_id,
        employee__isnull=True,
    ).update(employee=employee, updated_by=actor, updated_at=linked_at)
    if updated != 1:
        raise OnboardingLinkConflict
    OnboardingEmployeeLink.objects.create(
        card=card,
        employee=employee,
        employee_no=employee.employee_no,
        employee_name=profile_display_name(employee.profile),
        actor=actor,
        actor_name=profile_display_name(actor),
    )
    card.employee = employee
    card.updated_at = linked_at
    card.has_employee_link = True
    return card


def card_history(card_id):
    if not OnboardingCard.objects.filter(pk=card_id).exists():
        raise OnboardingNotFound
    changes = OnboardingStageChange.objects.filter(card_id=card_id)
    changes = [
        {
            "id": change.id,
            "from_column_id": change.from_column_id,
            "from_label": change.from_label,
            "from_phase": change.from_phase,
            "to_column_id": change.to_column_id,
            "to_label": change.to_label,
            "to_phase": change.to_phase,
            "actor_name": change.actor_name,
            "reason": change.reason,
            "created_at": change.created_at.isoformat(),
        }
        for change in changes
    ]
    employee_link = OnboardingEmployeeLink.objects.filter(card_id=card_id).first()
    return {
        "changes": changes,
        "employee_link": {
            "employee_id": employee_link.employee_id,
            "employee_no": employee_link.employee_no,
            "employee_name": employee_link.employee_name,
            "actor_name": employee_link.actor_name,
            "created_at": employee_link.created_at.isoformat(),
        } if employee_link else None,
    }
