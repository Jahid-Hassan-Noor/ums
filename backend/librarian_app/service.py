from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from admin_app.models import Profile
from librarian_app.models import BookAcquisitionRequest, BookCopy, BorrowingLimit, BorrowRequest, Fine as LibraryFine, Laptop, LibraryRoom, Loan
from notifications_package.service import notify_profile, notify_roles


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


def get_borrowing_limit(student):
    """Return the BorrowingLimit for this student, falling back to the default."""
    personal = getattr(student, "borrowing_limit", None)
    if personal:
        return personal
    default = BorrowingLimit.objects.filter(is_default=True).first()
    if default:
        return default
    # Fallback: no limit configured, use sensible defaults
    return type(
        "FallbackLimit",
        (),
        {
            "id": None,
            "pk": None,
            "student": None,
            "student_id": None,
            "max_borrow_at_a_time": 3,
            "max_keep_at_a_time": 5,
            "is_default": True,
            "created_at": None,
            "updated_at": None,
        },
    )()


def _check_asset_borrowing_limits(student, asset_type):
    """Enforce borrowing limits before issuing a loan."""
    limit = get_borrowing_limit(student)
    if asset_type == BorrowRequest.ASSET_BOOK:
        active_book_loans = Loan.objects.filter(
            student=student,
            status=Loan.STATUS_ACTIVE,
            book_copy__isnull=False,
        ).count()
        if active_book_loans >= limit.max_keep_at_a_time:
            raise ValidationError(
                f"You already hold {active_book_loans} book(s). "
                f"Return a book before borrowing another (limit: {limit.max_keep_at_a_time})."
            )
        if active_book_loans >= limit.max_borrow_at_a_time:
            raise ValidationError(
                f"You have reached the borrow limit of {limit.max_borrow_at_a_time} book(s) at a time."
            )
    elif asset_type == BorrowRequest.ASSET_LAPTOP:
        active_laptop_loans = Loan.objects.filter(
            student=student,
            status=Loan.STATUS_ACTIVE,
            laptop__isnull=False,
        ).count()
        if active_laptop_loans >= 1:
            raise ValidationError("You already have a laptop on loan. Return it before borrowing another.")
    elif asset_type == BorrowRequest.ASSET_ROOM:
        active_room_loans = Loan.objects.filter(
            student=student,
            status=Loan.STATUS_ACTIVE,
            room__isnull=False,
        ).count()
        if active_room_loans >= 1:
            raise ValidationError("You already have a room allocated. Return it before reserving another.")


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

    # Check library service availability
    from admin_app.settings_registry import all_settings
    lib_settings = all_settings().get("librarian_library", {})
    if book_copy and not bool(lib_settings.get("books_enabled", True)):
        raise ValidationError("Book borrowing is temporarily unavailable.")
    if laptop and not bool(lib_settings.get("laptops_enabled", True)):
        raise ValidationError("Laptop borrowing is currently disabled.")
    if room and not bool(lib_settings.get("rooms_enabled", True)):
        raise ValidationError("Discussion room booking is currently disabled.")

    _check_asset_borrowing_limits(student, asset_type="book" if book_copy else "laptop" if laptop else "room")

    loan = Loan.objects.create(
        student=student,
        book_copy=book_copy,
        laptop=laptop,
        room=room,
        request=request,
        assigned_by=assigned_by,
        due_at=due_at,
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

from datetime import timedelta

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
    if loan.renewal_count >= loan.max_renewals:
        raise ValidationError("Maximum renewals reached for this loan.")
    # Determine new due date
    if due_at:
        new_due = due_at
    else:
        # default extension of 14 days from current due
        new_due = loan.due_at + timedelta(days=14)
    loan.due_at = new_due
    loan.renewal_count += 1
    loan.save(update_fields=["due_at", "renewal_count", "updated_at"])
    # Notify student
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
def apply_overdue_fine(loan_id, *, daily_rate=1.0):
    loan = Loan.objects.select_for_update().filter(pk=loan_id).first()
    if not loan:
        raise ValidationError("Loan not found.")
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
