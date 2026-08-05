from django.utils import timezone
from django.db.models import Q

from admin_app.models import Profile
from admin_app.settings_registry import (
    helpdesk_assignment_rule,
    helpdesk_category_label,
    helpdesk_reference,
    helpdesk_status_label,
)
from core.common.profiles import profile_display_name, profile_identifier
from notifications_package.service import notify_profile, notify_profiles
from technician_app.models import HelpdeskTicket, HelpdeskTicketUpdate


def ticket_payload(ticket):
    return {
        "id": ticket.id,
        "reference": helpdesk_reference(ticket.id),
        "category": ticket.category,
        "category_label": helpdesk_category_label(ticket.category),
        "subject": ticket.subject,
        "description": ticket.description,
        "location": ticket.location,
        "status": ticket.status,
        "status_label": helpdesk_status_label(ticket.status),
        "resolution_notes": ticket.resolution_notes,
        "student": {
            "id": ticket.student_id,
            "name": profile_display_name(ticket.student),
            "student_id": profile_identifier(ticket.student),
            "email": ticket.student.user.email,
            "phone": ticket.student.phone,
        },
        "assigned_to": (
            {
                "id": ticket.assigned_to_id,
                "name": profile_display_name(ticket.assigned_to),
            }
            if ticket.assigned_to_id
            else None
        ),
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
        "updates": [
            {
                "id": update.id,
                "status": update.status,
                "status_label": helpdesk_status_label(update.status),
                "note": update.note,
                "author_name": profile_display_name(update.author) if update.author_id else "System",
                "created_at": update.created_at.isoformat(),
            }
            for update in ticket.updates.all()
        ],
    }


def ticket_queryset():
    return HelpdeskTicket.objects.select_related(
        "student__user",
        "assigned_to__user",
    ).prefetch_related("updates__author__user")


def active_technician_profiles():
    return Profile.objects.select_related(
        "user",
        "technician_detail",
        "technician_detail__school",
        "technician_detail__center",
        "technician_detail__department",
        "technician_detail__unit",
    ).filter(
        role=Profile.ROLE_TECHNICIAN,
        is_active=True,
        user__is_active=True,
    )


def _technician_profiles_for_rule(rule):
    owner_type = rule.get("owner_type")
    owner_code = str(rule.get("owner_code") or "").strip()
    if not owner_type or not owner_code:
        return active_technician_profiles().none()

    lookup = Q()
    if owner_type == "technician_id":
        lookup = Q(technician_detail__technician_id__iexact=owner_code)
    elif owner_type == "unit":
        lookup = Q(technician_detail__unit__code__iexact=owner_code)
    elif owner_type == "department":
        lookup = Q(technician_detail__department__code__iexact=owner_code)
    elif owner_type == "center":
        lookup = Q(technician_detail__center__code__iexact=owner_code)
    elif owner_type == "school":
        lookup = Q(technician_detail__school__code__iexact=owner_code)
    return active_technician_profiles().filter(lookup).distinct()


def default_assignee_for_category(category):
    rule = helpdesk_assignment_rule(category)
    if not rule:
        return None
    return _technician_profiles_for_rule(rule).order_by(
        "user__first_name",
        "user__last_name",
        "user__username",
    ).first()


def technician_recipients_for_category(category):
    rule = helpdesk_assignment_rule(category)
    if not rule:
        return active_technician_profiles()
    scoped = _technician_profiles_for_rule(rule)
    return scoped if scoped.exists() else active_technician_profiles()


def notify_technicians(ticket):
    notify_profiles(
        technician_recipients_for_category(ticket.category),
        actor=ticket.student,
        event_type="helpdesk.created",
        verb=f"New service desk ticket {ticket.subject}",
        data={"ticket_id": ticket.id, "category": ticket.category},
        url="/technician/helpdesk",
    )


def update_ticket(ticket, technician, status_value, note):
    ticket.status = status_value
    ticket.assigned_to = ticket.assigned_to or technician
    if status_value in {HelpdeskTicket.STATUS_ADDRESSED, HelpdeskTicket.STATUS_IN_PROGRESS}:
        ticket.addressed_at = ticket.addressed_at or timezone.now()
        ticket.solved_at = None
    elif status_value == HelpdeskTicket.STATUS_SOLVED:
        ticket.addressed_at = ticket.addressed_at or timezone.now()
        ticket.solved_at = timezone.now()
        if note:
            ticket.resolution_notes = note
    elif status_value == HelpdeskTicket.STATUS_SUBMITTED:
        ticket.solved_at = None
    ticket.save()
    HelpdeskTicketUpdate.objects.create(
        ticket=ticket,
        author=technician,
        status=status_value,
        note=note,
    )
    notify_profile(
        ticket.student,
        actor=technician,
        event_type="helpdesk.status_changed",
        verb=f"{helpdesk_status_label(ticket.status)}: {ticket.subject}",
        data={"ticket_id": ticket.id, "status": ticket.status},
        url="/student/ict-helpdesk",
    )
    return ticket
