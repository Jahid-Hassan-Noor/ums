"""In-app and email notifications for the Fine/Charge feature."""
from notifications_package.service import notify_profile, notify_roles
from admin_app.models import Profile


def notify_fine_issued(*, fine):
    """
    Notify the student that a new fine has been issued.
    Also notify all accountants (so they have a record).
    """
    student = fine.student
    due_str = f" — due by {fine.due_date.strftime('%d %b %Y %H:%M')}" if fine.due_date else ""
    amount_str = f"{fine.currency} {fine.amount}"
    url = f"/student/fines"

    notify_profile(
        student,
        event_type="fine_issued",
        verb=f"A fine of {amount_str} has been issued to you: {fine.reason}{due_str}.",
        data={"fine_id": fine.pk, "amount": str(fine.amount), "reason": fine.reason},
        url=url,
        email_subject="AIU Portal – New Fine Issued",
        email_message=(
            f"A fine of {amount_str} has been issued to your account.\n\n"
            f"Reason: {fine.reason}\n"
            f"Description: {fine.description or 'N/A'}\n"
            f"Amount: {amount_str}{due_str}\n\n"
            f"You can pay this fine online via the AIU Student Portal."
        ),
    )


def notify_fine_paid(*, fine):
    """Notify the student that their fine payment was received."""
    student = fine.student
    amount_str = f"{fine.currency} {fine.amount}"
    url = f"/student/fines"

    notify_profile(
        student,
        event_type="fine_paid",
        verb=f"Your fine of {amount_str} ({fine.reason}) has been paid successfully. Thank you.",
        data={"fine_id": fine.pk, "amount": str(fine.amount), "reason": fine.reason},
        url=url,
        email_subject="AIU Portal – Fine Payment Received",
        email_message=(
            f"Your fine payment has been received.\n\n"
            f"Reason: {fine.reason}\n"
            f"Amount paid: {amount_str}\n\n"
            f"Thank you. Your account is now clear of this charge."
        ),
    )


def notify_fine_deducted(*, fine):
    """Notify the student that the fine was manually deducted from their meal allowance."""
    student = fine.student
    amount_str = f"{fine.currency} {fine.amount}"
    url = f"/student/fines"
    note_str = f"\n\nNote from accountant: {fine.deduction_note}" if fine.deduction_note else ""

    notify_profile(
        student,
        event_type="fine_deducted",
        verb=(
            f"A fine of {amount_str} ({fine.reason}) has been deducted from your meal allowance.{note_str}"
        ),
        data={"fine_id": fine.pk, "amount": str(fine.amount), "reason": fine.reason},
        url=url,
        email_subject="AIU Portal – Fine Deducted from Meal Allowance",
        email_message=(
            f"A fine has been deducted from your meal allowance.\n\n"
            f"Reason: {fine.reason}\n"
            f"Amount deducted: {amount_str}{note_str}\n\n"
            f"If you have any questions, please contact the Finance Office."
        ),
    )


def notify_fine_overdue(*, fine):
    """Notify the student that their fine is overdue and will be deducted manually."""
    student = fine.student
    amount_str = f"{fine.currency} {fine.amount}"
    url = f"/student/fines"

    notify_profile(
        student,
        event_type="fine_overdue",
        verb=f"Your fine of {amount_str} ({fine.reason}) is overdue. It will be deducted from your meal allowance.",
        data={"fine_id": fine.pk, "amount": str(fine.amount), "reason": fine.reason},
        url=url,
        email_subject="AIU Portal – Fine Overdue Notice",
        email_message=(
            f"Your fine payment is overdue.\n\n"
            f"Reason: {fine.reason}\n"
            f"Amount: {amount_str}\n\n"
            f"The amount will now be processed for manual deduction from your meal allowance. "
            f"Please contact the Finance Office if you have any questions."
        ),
    )
