from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from admin_app.models import Profile
from core.common.money import format_money, parse_decimal
from core.common.request_utils import parse_bool, parse_int
from librarian_app.models import BookAcquisitionRequest, BookCopy, BorrowingLimit, BorrowRequest, Fine as LibraryFine, Laptop, LibraryRoom, Loan
from notifications_package.service import notify_profile, notify_roles


ASSET_OTHER = "other_asset"

LIBRARY_ASSET_LABELS = {
    BorrowRequest.ASSET_BOOK: "Books",
    BorrowRequest.ASSET_LAPTOP: "Laptops",
    BorrowRequest.ASSET_ROOM: "Discussion rooms",
    ASSET_OTHER: "Other assets",
}

LIBRARY_POLICY_DEFAULTS = {
    "books_enabled": True,
    "laptops_enabled": True,
    "rooms_enabled": True,
    "other_assets_enabled": False,
    "book_requests_enabled": True,
    "laptop_requests_enabled": True,
    "room_reservations_enabled": True,
    "other_asset_requests_enabled": False,
    "book_max_borrow_at_a_time": 3,
    "book_max_keep_at_a_time": 5,
    "laptop_max_borrow_at_a_time": 1,
    "laptop_max_keep_at_a_time": 1,
    "room_max_borrow_at_a_time": 1,
    "room_max_keep_at_a_time": 1,
    "other_asset_max_borrow_at_a_time": 1,
    "other_asset_max_keep_at_a_time": 1,
    "book_loan_period_days": 14,
    "laptop_loan_period_days": 7,
    "room_loan_period_hours": 2,
    "other_asset_loan_period_days": 7,
    "book_max_renewals": 2,
    "laptop_max_renewals": 0,
    "room_max_renewals": 0,
    "other_asset_max_renewals": 0,
    "book_renewal_period_days": 14,
    "laptop_renewal_period_days": 7,
    "room_renewal_period_hours": 1,
    "other_asset_renewal_period_days": 7,
    "book_daily_fine_amount": "1.00",
    "laptop_daily_fine_amount": "5.00",
    "room_daily_fine_amount": "0.00",
    "other_asset_daily_fine_amount": "1.00",
}

LIBRARY_BOOL_POLICY_KEYS = {
    key for key, value in LIBRARY_POLICY_DEFAULTS.items() if isinstance(value, bool)
}
LIBRARY_DECIMAL_POLICY_KEYS = {
    "book_daily_fine_amount",
    "laptop_daily_fine_amount",
    "room_daily_fine_amount",
    "other_asset_daily_fine_amount",
}
LIBRARY_INT_POLICY_KEYS = set(LIBRARY_POLICY_DEFAULTS) - LIBRARY_BOOL_POLICY_KEYS - LIBRARY_DECIMAL_POLICY_KEYS
LIBRARY_POLICY_KEYS = set(LIBRARY_POLICY_DEFAULTS)

_ASSET_CONFIG = {
    BorrowRequest.ASSET_BOOK: {
        "enabled_key": "books_enabled",
        "request_key": "book_requests_enabled",
        "prefix": "book",
        "period_key": "book_loan_period_days",
        "period_unit": "days",
        "renewal_period_key": "book_renewal_period_days",
        "renewal_unit": "days",
        "fine_key": "book_daily_fine_amount",
    },
    BorrowRequest.ASSET_LAPTOP: {
        "enabled_key": "laptops_enabled",
        "request_key": "laptop_requests_enabled",
        "prefix": "laptop",
        "period_key": "laptop_loan_period_days",
        "period_unit": "days",
        "renewal_period_key": "laptop_renewal_period_days",
        "renewal_unit": "days",
        "fine_key": "laptop_daily_fine_amount",
    },
    BorrowRequest.ASSET_ROOM: {
        "enabled_key": "rooms_enabled",
        "request_key": "room_reservations_enabled",
        "prefix": "room",
        "period_key": "room_loan_period_hours",
        "period_unit": "hours",
        "renewal_period_key": "room_renewal_period_hours",
        "renewal_unit": "hours",
        "fine_key": "room_daily_fine_amount",
    },
    ASSET_OTHER: {
        "enabled_key": "other_assets_enabled",
        "request_key": "other_asset_requests_enabled",
        "prefix": "other_asset",
        "period_key": "other_asset_loan_period_days",
        "period_unit": "days",
        "renewal_period_key": "other_asset_renewal_period_days",
        "renewal_unit": "days",
        "fine_key": "other_asset_daily_fine_amount",
    },
}


def _config_for_asset(asset_type):
    if asset_type not in _ASSET_CONFIG:
        raise ValidationError("Select a supported library asset type.")
    return _ASSET_CONFIG[asset_type]


def _asset_label(asset_type):
    return LIBRARY_ASSET_LABELS.get(asset_type, "Library assets").lower()


def _loan_filter_for_asset(asset_type):
    if asset_type == BorrowRequest.ASSET_BOOK:
        return {"book_copy__isnull": False}
    if asset_type == BorrowRequest.ASSET_LAPTOP:
        return {"laptop__isnull": False}
    if asset_type == BorrowRequest.ASSET_ROOM:
        return {"room__isnull": False}
    return {}


def asset_type_for_loan(loan):
    if loan.book_copy_id:
        return BorrowRequest.ASSET_BOOK
    if loan.laptop_id:
        return BorrowRequest.ASSET_LAPTOP
    if loan.room_id:
        return BorrowRequest.ASSET_ROOM
    return ASSET_OTHER


def _raw_library_settings():
    from admin_app.settings_registry import all_settings

    return all_settings().get("librarian_library", {})


def _decimal_policy_value(value, default):
    try:
        return format_money(parse_decimal(value, allow_zero=True))
    except ValidationError:
        return default


def library_policy_settings(values=None):
    if values is None:
        values = _raw_library_settings()
    elif "librarian_library" in values:
        values = values.get("librarian_library", {})

    policy = {}
    for key, default in LIBRARY_POLICY_DEFAULTS.items():
        raw_value = values.get(key, default)
        if key in LIBRARY_BOOL_POLICY_KEYS:
            policy[key] = parse_bool(raw_value, default=default)
        elif key in LIBRARY_DECIMAL_POLICY_KEYS:
            policy[key] = _decimal_policy_value(raw_value, default)
        else:
            parsed = parse_int(raw_value, default=default)
            minimum = 0 if key.endswith("_max_renewals") else 1
            policy[key] = parsed if parsed >= minimum else default

    for asset_type, config in _ASSET_CONFIG.items():
        prefix = config["prefix"]
        borrow_key = f"{prefix}_max_borrow_at_a_time"
        keep_key = f"{prefix}_max_keep_at_a_time"
        if policy[borrow_key] > policy[keep_key]:
            policy[borrow_key] = policy[keep_key]
    return policy


def _normalize_bool_update(key, value):
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    if token not in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
        raise ValidationError({key: "Provide true or false."})
    return parse_bool(value)


def _normalize_int_update(key, value):
    parsed = parse_int(value, default=None)
    if parsed is None:
        raise ValidationError({key: "Provide a valid whole number."})
    minimum = 0 if key.endswith("_max_renewals") else 1
    if parsed < minimum:
        raise ValidationError({key: f"Must be at least {minimum}."})
    if parsed > 24 and key.endswith("_period_hours"):
        raise ValidationError({key: "Must be 24 or less."})
    if parsed > 365 and key.endswith("_period_days"):
        raise ValidationError({key: "Must be 365 or less."})
    if parsed > 99 and key.endswith(("_at_a_time", "_keep_at_a_time")):
        raise ValidationError({key: "Must be 99 or less."})
    if parsed > 12 and key.endswith("_max_renewals"):
        raise ValidationError({key: "Must be 12 or less."})
    return parsed


def normalize_library_policy_updates(data):
    updates = {}
    for key in LIBRARY_POLICY_KEYS:
        if key not in data:
            continue
        if key in LIBRARY_BOOL_POLICY_KEYS:
            updates[key] = _normalize_bool_update(key, data[key])
        elif key in LIBRARY_DECIMAL_POLICY_KEYS:
            updates[key] = format_money(parse_decimal(data[key], field=key, allow_zero=True))
        else:
            updates[key] = _normalize_int_update(key, data[key])

    for asset_type, config in _ASSET_CONFIG.items():
        prefix = config["prefix"]
        borrow_key = f"{prefix}_max_borrow_at_a_time"
        keep_key = f"{prefix}_max_keep_at_a_time"
        borrow_value = updates.get(borrow_key)
        keep_value = updates.get(keep_key)
        if borrow_value is not None and keep_value is not None and borrow_value > keep_value:
            raise ValidationError({borrow_key: "Borrow limit cannot exceed holding limit."})
    return updates


def library_services_payload(policy=None):
    policy = policy or library_policy_settings()
    return {
        "books_enabled": bool(policy["books_enabled"]),
        "laptops_enabled": bool(policy["laptops_enabled"]),
        "rooms_enabled": bool(policy["rooms_enabled"]),
        "other_assets_enabled": bool(policy["other_assets_enabled"]),
    }


def library_asset_enabled(asset_type, policy=None):
    policy = policy or library_policy_settings()
    return bool(policy[_config_for_asset(asset_type)["enabled_key"]])


def library_requesting_enabled(asset_type, policy=None):
    policy = policy or library_policy_settings()
    config = _config_for_asset(asset_type)
    return library_asset_enabled(asset_type, policy) and bool(policy[config["request_key"]])


def enabled_library_asset_types(policy=None):
    policy = policy or library_policy_settings()
    return [
        asset_type
        for asset_type in (BorrowRequest.ASSET_BOOK, BorrowRequest.ASSET_LAPTOP, BorrowRequest.ASSET_ROOM)
        if library_asset_enabled(asset_type, policy)
    ]


def _duration_delta(asset_type, *, renewal=False, policy=None):
    policy = policy or library_policy_settings()
    config = _config_for_asset(asset_type)
    value = policy[config["renewal_period_key"] if renewal else config["period_key"]]
    unit = config["renewal_unit"] if renewal else config["period_unit"]
    if unit == "hours":
        return timedelta(hours=value)
    return timedelta(days=value)


def _duration_payload(asset_type, *, renewal=False, policy=None):
    policy = policy or library_policy_settings()
    config = _config_for_asset(asset_type)
    key = config["renewal_period_key"] if renewal else config["period_key"]
    unit = config["renewal_unit"] if renewal else config["period_unit"]
    value = policy[key]
    return {"value": value, "unit": unit, unit: value}


def default_due_at_for_asset(asset_type, *, from_time=None, policy=None):
    return (from_time or timezone.now()) + _duration_delta(asset_type, policy=policy)


def validate_due_at_for_asset(asset_type, due_at, *, borrowed_at=None, policy=None):
    if not due_at:
        raise ValidationError("Provide a valid due date and time.")
    policy = policy or library_policy_settings()
    start = borrowed_at or timezone.now()
    max_due_at = default_due_at_for_asset(asset_type, from_time=start, policy=policy)
    if due_at > max_due_at:
        duration = _duration_payload(asset_type, policy=policy)
        raise ValidationError(
            f"{LIBRARY_ASSET_LABELS[asset_type]} loans cannot exceed "
            f"{duration['value']} {duration['unit']}."
        )
    return due_at


def validate_library_service_available(asset_type, policy=None):
    if not library_asset_enabled(asset_type, policy):
        raise ValidationError(f"{LIBRARY_ASSET_LABELS[asset_type]} service is currently disabled.")


def validate_library_request_available(asset_type, policy=None):
    validate_library_service_available(asset_type, policy)
    if not library_requesting_enabled(asset_type, policy):
        raise ValidationError(f"Student requests for {_asset_label(asset_type)} are currently disabled.")


def _policy_limit_for_asset(asset_type, *, student=None, policy=None):
    policy = policy or library_policy_settings()
    if asset_type == BorrowRequest.ASSET_BOOK and student is not None:
        limit = get_borrowing_limit(student, policy=policy)
        return {
            "max_borrow_at_a_time": limit.max_borrow_at_a_time,
            "max_keep_at_a_time": limit.max_keep_at_a_time,
        }
    config = _config_for_asset(asset_type)
    prefix = config["prefix"]
    return {
        "max_borrow_at_a_time": policy[f"{prefix}_max_borrow_at_a_time"],
        "max_keep_at_a_time": policy[f"{prefix}_max_keep_at_a_time"],
    }


def library_policy_payload(*, student=None, policy=None):
    policy = policy or library_policy_settings()
    limits = {}
    loan_periods = {}
    renewal_rules = {}
    fine_rules = {}
    reservation_rules = {}
    service_types = []

    for asset_type, config in _ASSET_CONFIG.items():
        limits[asset_type] = _policy_limit_for_asset(asset_type, student=student, policy=policy)
        loan_periods[asset_type] = _duration_payload(asset_type, policy=policy)
        renewal_rules[asset_type] = {
            "max_renewals": policy[f"{config['prefix']}_max_renewals"],
            "period": _duration_payload(asset_type, renewal=True, policy=policy),
        }
        fine_rules[asset_type] = {
            "daily_rate": policy[config["fine_key"]],
        }
        reservation_rules[asset_type] = {
            "enabled": bool(policy[config["request_key"]]),
        }
        service_types.append(
            {
                "key": asset_type,
                "label": LIBRARY_ASSET_LABELS[asset_type],
                "enabled": bool(policy[config["enabled_key"]]),
                "requesting_enabled": bool(policy[config["request_key"]]),
                "supported": asset_type != ASSET_OTHER,
            }
        )

    return {
        **library_services_payload(policy),
        "service_types": service_types,
        "limits": limits,
        "loan_periods": loan_periods,
        "fine_rules": fine_rules,
        "renewal_rules": renewal_rules,
        "reservation_rules": reservation_rules,
    }


def _active_asset_loan_count(student, asset_type):
    return Loan.objects.filter(
        student=student,
        status=Loan.STATUS_ACTIVE,
        **_loan_filter_for_asset(asset_type),
    ).count()


def _pending_asset_request_count(student, asset_type):
    return BorrowRequest.objects.filter(
        student=student,
        asset_type=asset_type,
        status=BorrowRequest.STATUS_PENDING,
    ).count()


def enforce_library_request_limit(student, asset_type, policy=None):
    policy = policy or library_policy_settings()
    limit = _policy_limit_for_asset(asset_type, student=student, policy=policy)
    active_count = _active_asset_loan_count(student, asset_type)
    pending_count = _pending_asset_request_count(student, asset_type)
    held_count = active_count + pending_count
    label = _asset_label(asset_type)
    if held_count >= limit["max_keep_at_a_time"]:
        raise ValidationError(
            f"You already hold or have pending requests for {held_count} {label}. "
            f"Return or close one before requesting another "
            f"(limit: {limit['max_keep_at_a_time']})."
        )
    if held_count >= limit["max_borrow_at_a_time"]:
        raise ValidationError(
            f"You have reached the request limit of {limit['max_borrow_at_a_time']} {label}."
        )


def borrow_request_asset_label(borrow_request):
    if borrow_request.book_id:
        return borrow_request.book.title
    if borrow_request.laptop_id:
        return borrow_request.laptop.asset_tag
    if borrow_request.room_id:
        return borrow_request.room.name
    return borrow_request.get_asset_type_display()


def loan_asset_label(loan):
    if loan.book_copy_id:
        return loan.book_copy.book.title
    if loan.laptop_id:
        return loan.laptop.asset_tag
    if loan.room_id:
        return loan.room.name
    return "library item"


def _truncate_reason(value, max_length=500):
    value = str(value)
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 3]}..."


def _library_loan_marker(loan):
    return f"Library loan #{loan.pk}"


def _library_finance_description(loan, *, charge_label, note=""):
    parts = [
        f"{_library_loan_marker(loan)} for {loan_asset_label(loan)}.",
        f"Charge type: {charge_label}.",
    ]
    if loan.due_at:
        parts.append(f"Loan due at: {loan.due_at.isoformat()}.")
    if note:
        parts.append(f"Library note: {note}")
    return "\n".join(parts)


def _upsert_library_finance_fine(loan, *, reason, amount, description, due_date=None):
    from accountant_app.fine_service import create_fine
    from accountant_app.models import Fine as FinanceFine

    reason = _truncate_reason(reason)
    amount = Decimal(str(amount))
    marker = _library_loan_marker(loan)
    fine = (
        FinanceFine.objects.filter(
            student=loan.student,
            reason=reason,
            description__contains=marker,
            status__in=[FinanceFine.STATUS_PENDING, FinanceFine.STATUS_OVERDUE],
        )
        .order_by("-created_at")
        .first()
    )

    if fine:
        fine.amount = amount
        fine.description = description
        fine.due_date = due_date
        fine.checkout_url = ""
        fine.gateway_bill_code = ""
        fine.status = FinanceFine.STATUS_PENDING
        fine.save(
            update_fields=[
                "amount",
                "description",
                "due_date",
                "checkout_url",
                "gateway_bill_code",
                "status",
                "updated_at",
            ]
        )
        return fine

    return create_fine(
        accountant=None,
        student_profile=loan.student,
        reason=reason,
        amount=amount,
        description=description,
        due_date=due_date,
    )


def notify_librarians_of_request(borrow_request):
    notify_roles(
        [Profile.ROLE_LIBRARIAN],
        actor=borrow_request.student,
        event_type="library.borrow_requested",
        verb=f"New library request for {borrow_request_asset_label(borrow_request)}.",
        data={
            "borrow_request_id": borrow_request.id,
            "asset_type": borrow_request.asset_type,
            "student_id": borrow_request.student_id,
        },
        url="/librarian/circulation",
    )


def notify_librarians_of_room_reservation_cancelled(borrow_request):
    notify_roles(
        [Profile.ROLE_LIBRARIAN],
        actor=borrow_request.student,
        event_type="library.room_reservation_cancelled",
        verb=f"Room reservation cancelled for {borrow_request_asset_label(borrow_request)}.",
        data={
            "borrow_request_id": borrow_request.id,
            "asset_type": borrow_request.asset_type,
            "student_id": borrow_request.student_id,
        },
        url="/librarian/circulation",
    )


def notify_librarians_of_book_acquisition_request(acquisition_request):
    notify_roles(
        [Profile.ROLE_LIBRARIAN],
        actor=acquisition_request.student,
        event_type="library.book_acquisition_requested",
        verb=f"New request to add {acquisition_request.title} by {acquisition_request.author}.",
        data={
            "book_acquisition_request_id": acquisition_request.id,
            "student_id": acquisition_request.student_id,
        },
        url="/librarian/books",
    )


def notify_student_request_decision(borrow_request):
    notify_profile(
        borrow_request.student,
        actor=borrow_request.reviewed_by,
        event_type="library.request_decided",
        verb=(
            f"Your library request for {borrow_request_asset_label(borrow_request)} "
            f"was {borrow_request.get_status_display().lower()}."
        ),
        data={
            "borrow_request_id": borrow_request.id,
            "status": borrow_request.status,
            "review_note": borrow_request.review_note,
        },
        url=(
            "/student/library/laptops"
            if borrow_request.asset_type == BorrowRequest.ASSET_LAPTOP
            else "/student/library/rooms"
            if borrow_request.asset_type == BorrowRequest.ASSET_ROOM
            else "/student/library/books"
        ),
    )


def notify_student_book_acquisition_decision(acquisition_request):
    notify_profile(
        acquisition_request.student,
        actor=acquisition_request.reviewed_by,
        event_type="library.book_acquisition_decided",
        verb=(
            f"Your request to add {acquisition_request.title} "
            f"was marked {acquisition_request.get_status_display().lower()}."
        ),
        data={
            "book_acquisition_request_id": acquisition_request.id,
            "status": acquisition_request.status,
            "review_note": acquisition_request.review_note,
            "added_book_id": acquisition_request.added_book_id,
        },
        url="/student/library/books",
    )


def get_borrowing_limit(student, *, policy=None):
    """Return the BorrowingLimit for this student, falling back to the default."""
    if student is not None:
        personal = getattr(student, "borrowing_limit", None)
        if personal:
            return personal
    default = BorrowingLimit.objects.filter(is_default=True).first()
    if default:
        return default
    policy = policy or library_policy_settings()
    return type(
        "FallbackLimit",
        (),
        {
            "id": None,
            "pk": None,
            "student": None,
            "student_id": None,
            "max_borrow_at_a_time": policy["book_max_borrow_at_a_time"],
            "max_keep_at_a_time": policy["book_max_keep_at_a_time"],
            "is_default": True,
            "created_at": None,
            "updated_at": None,
        },
    )()


def _check_asset_borrowing_limits(student, asset_type, *, policy=None):
    """Enforce borrowing limits before issuing a loan."""
    policy = policy or library_policy_settings()
    limit = _policy_limit_for_asset(asset_type, student=student, policy=policy)
    active_count = _active_asset_loan_count(student, asset_type)
    label = _asset_label(asset_type)
    if active_count >= limit["max_keep_at_a_time"]:
        raise ValidationError(
            f"You already hold {active_count} {label}. "
            f"Return one before borrowing another (limit: {limit['max_keep_at_a_time']})."
        )
    if active_count >= limit["max_borrow_at_a_time"]:
        raise ValidationError(
            f"You have reached the borrow limit of {limit['max_borrow_at_a_time']} {label}."
        )


@transaction.atomic
def issue_loan(
    *,
    student_id,
    assigned_by,
    due_at,
    book_copy_id=None,
    laptop_id=None,
    room_id=None,
    request_id=None,
    notes="",
):
    student = Profile.objects.select_for_update().filter(
        pk=student_id,
        role=Profile.ROLE_STUDENT,
        is_active=True,
    ).first()
    if not student:
        raise ValidationError("Select an active student.")

    request = None
    if request_id:
        request = BorrowRequest.objects.select_for_update().filter(
            pk=request_id,
            status=BorrowRequest.STATUS_PENDING,
        ).first()
        if not request:
            raise ValidationError("The borrowing request is not pending.")
        if request.student_id != student.id:
            raise ValidationError("The request belongs to another student.")

    book_copy = None
    laptop = None
    room = None
    if sum(bool(asset_id) for asset_id in (book_copy_id, laptop_id, room_id)) != 1:
        raise ValidationError("Assign exactly one book copy, laptop, or discussion room.")
    if book_copy_id:
        book_copy = BookCopy.objects.select_for_update().filter(pk=book_copy_id).first()
        if not book_copy or book_copy.status != BookCopy.STATUS_AVAILABLE:
            raise ValidationError("The selected book copy is not available.")
        if request and (request.asset_type != BorrowRequest.ASSET_BOOK or request.book_id != book_copy.book_id):
            raise ValidationError("The selected copy does not match the borrowing request.")
    if laptop_id:
        laptop = Laptop.objects.select_for_update().filter(pk=laptop_id).first()
        if not laptop or laptop.status != Laptop.STATUS_AVAILABLE:
            raise ValidationError("The selected laptop is not available.")
        if request and (request.asset_type != BorrowRequest.ASSET_LAPTOP or request.laptop_id != laptop.id):
            raise ValidationError("The selected laptop does not match the borrowing request.")
    if room_id:
        room = LibraryRoom.objects.select_for_update().filter(pk=room_id).first()
        if not room or room.status != LibraryRoom.STATUS_AVAILABLE:
            raise ValidationError("The selected discussion room is not available.")
        if room.loans.filter(status=Loan.STATUS_ACTIVE).exists():
            raise ValidationError("The selected discussion room is already in use.")
        if request and (request.asset_type != BorrowRequest.ASSET_ROOM or request.room_id != room.id):
            raise ValidationError("The selected discussion room does not match the reservation request.")
        if not request and room.reservation_requests.filter(status=BorrowRequest.STATUS_PENDING).exists():
            raise ValidationError("This discussion room is reserved for another student.")

    asset_type = (
        BorrowRequest.ASSET_BOOK
        if book_copy
        else BorrowRequest.ASSET_LAPTOP
        if laptop
        else BorrowRequest.ASSET_ROOM
    )
    policy = library_policy_settings()
    validate_library_service_available(asset_type, policy)
    borrowed_at = timezone.now()
    validate_due_at_for_asset(asset_type, due_at, borrowed_at=borrowed_at, policy=policy)
    _check_asset_borrowing_limits(student, asset_type=asset_type, policy=policy)

    loan = Loan.objects.create(
        student=student,
        book_copy=book_copy,
        laptop=laptop,
        room=room,
        request=request,
        assigned_by=assigned_by,
        borrowed_at=borrowed_at,
        due_at=due_at,
        max_renewals=policy[f"{_config_for_asset(asset_type)['prefix']}_max_renewals"],
        notes=notes,
    )
    if book_copy:
        book_copy.status = BookCopy.STATUS_LOANED
        book_copy.save(update_fields=["status", "updated_at"])
    if laptop:
        laptop.status = Laptop.STATUS_LOANED
        laptop.save(update_fields=["status", "updated_at"])
    if room:
        room.status = LibraryRoom.STATUS_IN_USE
        room.save(update_fields=["status", "updated_at"])
    if request:
        request.status = BorrowRequest.STATUS_FULFILLED
        request.reviewed_by = assigned_by
        request.save(update_fields=["status", "reviewed_by", "updated_at"])
    notify_profile(
        student,
        actor=assigned_by,
        event_type="library.loan_issued",
        verb=(
            f"Room key allocated for {loan_asset_label(loan)}."
            if loan.room_id
            else f"Library loan issued for {loan_asset_label(loan)}."
        ),
        data={
            "loan_id": loan.id,
            "borrow_request_id": request.id if request else None,
            "due_at": loan.due_at.isoformat(),
        },
        url=(
            "/student/library/laptops"
            if loan.laptop_id
            else "/student/library/rooms"
            if loan.room_id
            else "/student/library/books"
        ),
    )
    return loan


@transaction.atomic
def cancel_room_reservation(request_id, *, student):
    borrow_request = (
        BorrowRequest.objects.select_for_update()
        .select_related("student", "student__user")
        .filter(
            pk=request_id,
            student=student,
            asset_type=BorrowRequest.ASSET_ROOM,
        )
        .first()
    )
    if not borrow_request:
        raise ValidationError("Room reservation request not found.")
    if borrow_request.status != BorrowRequest.STATUS_PENDING:
        raise ValidationError("Only pending room reservations can be cancelled.")

    borrow_request.status = BorrowRequest.STATUS_CANCELLED
    borrow_request.save(update_fields=["status", "updated_at"])
    notify_librarians_of_room_reservation_cancelled(borrow_request)
    return borrow_request


@transaction.atomic
def return_loan(loan_id, *, returned_by=None, condition_notes=""):
    loan = Loan.objects.select_for_update().filter(pk=loan_id, status=Loan.STATUS_ACTIVE).first()
    if not loan:
        raise ValidationError("Active loan not found.")
    if loan.book_copy_id:
        copy = BookCopy.objects.select_for_update().get(pk=loan.book_copy_id)
        copy.status = BookCopy.STATUS_AVAILABLE
        copy.condition_notes = condition_notes or copy.condition_notes
        copy.save(update_fields=["status", "condition_notes", "updated_at"])
    if loan.laptop_id:
        laptop = Laptop.objects.select_for_update().get(pk=loan.laptop_id)
        laptop.status = Laptop.STATUS_AVAILABLE
        laptop.condition_notes = condition_notes or laptop.condition_notes
        laptop.save(update_fields=["status", "condition_notes", "updated_at"])
    if loan.room_id:
        room = LibraryRoom.objects.select_for_update().get(pk=loan.room_id)
        room.status = LibraryRoom.STATUS_AVAILABLE
        room.save(update_fields=["status", "updated_at"])
    loan.status = Loan.STATUS_RETURNED
    loan.returned_at = timezone.now()
    loan.return_condition_notes = condition_notes
    loan.save(update_fields=["status", "returned_at", "return_condition_notes", "updated_at"])
    notify_profile(
        loan.student,
        actor=returned_by,
        event_type="library.loan_returned",
        verb=(
            f"Room key returned for {loan_asset_label(loan)}; the room is available again."
            if loan.room_id
            else f"Library return recorded for {loan_asset_label(loan)}."
        ),
        data={"loan_id": loan.id, "returned_at": loan.returned_at.isoformat()},
        url=(
            "/student/library/laptops"
            if loan.laptop_id
            else "/student/library/rooms"
            if loan.room_id
            else "/student/library/books"
        ),
    )
    return loan

@transaction.atomic
def renew_loan(loan_id, *, due_at=None, requested_by=None):
    """Renew an active loan, extending its due date within renewal limits.

    Args:
        loan_id: ID of the Loan to renew.
        due_at: Optional new due datetime. If omitted, extends by 14 days.
        requested_by: Profile performing the renewal (e.g., librarian).
    """
    loan = Loan.objects.select_for_update().filter(pk=loan_id, status=Loan.STATUS_ACTIVE).first()
    if not loan:
        raise ValidationError("Active loan not found.")
    asset_type = asset_type_for_loan(loan)
    policy = library_policy_settings()
    config = _config_for_asset(asset_type)
    max_renewals = policy[f"{config['prefix']}_max_renewals"]
    if loan.renewal_count >= max_renewals:
        raise ValidationError("Maximum renewals reached for this loan.")
    if due_at:
        new_due = due_at
    else:
        new_due = loan.due_at + _duration_delta(asset_type, renewal=True, policy=policy)
    renewal_limit_due = loan.due_at + _duration_delta(asset_type, renewal=True, policy=policy)
    if new_due > renewal_limit_due:
        duration = _duration_payload(asset_type, renewal=True, policy=policy)
        raise ValidationError(
            f"{LIBRARY_ASSET_LABELS[asset_type]} renewals cannot exceed "
            f"{duration['value']} {duration['unit']}."
        )
    loan.due_at = new_due
    loan.renewal_count += 1
    loan.max_renewals = max_renewals
    loan.save(update_fields=["due_at", "renewal_count", "max_renewals", "updated_at"])
    if requested_by:
        notify_profile(
            loan.student,
            actor=requested_by,
            event_type="library.loan_renewed",
            verb=f"Your loan for {loan_asset_label(loan)} has been renewed. New due date: {new_due.isoformat()}.",
            data={"loan_id": loan.id, "new_due_at": new_due.isoformat()},
            url="/student/library/books",
        )
    return loan

def _calculate_overdue_fine(loan, daily_rate=1.0):
    """Calculate overdue fine based on days past due.
    Returns a Decimal amount.
    """
    if loan.due_at >= timezone.now():
        return 0
    days_overdue = (timezone.now() - loan.due_at).days
    return Decimal(days_overdue) * Decimal(str(daily_rate))

@transaction.atomic
def apply_overdue_fine(loan_id, *, daily_rate=None):
    loan = Loan.objects.select_for_update().filter(pk=loan_id).first()
    if not loan:
        raise ValidationError("Loan not found.")
    asset_type = asset_type_for_loan(loan)
    policy = library_policy_settings()
    if daily_rate in (None, ""):
        daily_rate = policy[_config_for_asset(asset_type)["fine_key"]]
    else:
        daily_rate = parse_decimal(daily_rate, field="daily_rate", allow_zero=True)
    fine_amount = _calculate_overdue_fine(loan, daily_rate)
    if fine_amount > 0:
        loan.fine_amount = fine_amount
        loan.fine_paid = False
        loan.save(update_fields=["fine_amount", "fine_paid", "updated_at"])
        _upsert_library_finance_fine(
            loan,
            reason=f"Library overdue fine for {loan_asset_label(loan)}",
            amount=fine_amount,
            description=_library_finance_description(loan, charge_label="Overdue loan"),
            due_date=loan.due_at,
        )
    return loan

@transaction.atomic
def waive_fine(loan_id, *, waived_by, note=""):
    loan = Loan.objects.select_for_update().filter(pk=loan_id).first()
    if not loan:
        raise ValidationError("Loan not found.")
    if loan.fine_amount == 0:
        raise ValidationError("No fine to waive.")
    loan.fine_paid = True
    loan.save(update_fields=["fine_paid", "updated_at"])
    # Record a Fine entry marked as waived for audit purposes
    LibraryFine.objects.create(loan=loan, amount=loan.fine_amount, waived=True, note=note)
    # Notify student
    notify_profile(
        loan.student,
        actor=waived_by,
        event_type="library.fine_waived",
        verb=f"Fine of {loan.fine_amount} for loan {loan.id} has been waived.",
        data={"loan_id": loan.id},
        url="/student/library/loans",
    )
    return loan

@transaction.atomic
def mark_lost(loan_id, *, lost_charge, marked_by, note=""):
    loan = Loan.objects.select_for_update().filter(pk=loan_id, status=Loan.STATUS_ACTIVE).first()
    if not loan:
        raise ValidationError("Active loan not found.")
    loan.is_lost = True
    loan.lost_charge = lost_charge
    loan.fine_amount = lost_charge
    loan.fine_paid = False
    loan.status = Loan.STATUS_LOST
    loan.save(update_fields=["is_lost", "lost_charge", "fine_amount", "fine_paid", "status", "updated_at"])
    # Create Fine entry for lost charge
    _upsert_library_finance_fine(
        loan,
        reason=f"Library lost item charge for {loan_asset_label(loan)}",
        amount=lost_charge,
        description=_library_finance_description(loan, charge_label="Lost item", note=note),
    )
    # Notify student
    notify_profile(
        loan.student,
        actor=marked_by,
        event_type="library.item_lost",
        verb=f"Your loan for {loan_asset_label(loan)} has been marked as lost. Charge: {lost_charge}.",
        data={"loan_id": loan.id, "lost_charge": lost_charge},
        url="/student/library/loans",
    )
    return loan
