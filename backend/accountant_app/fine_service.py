"""Fine / charge service functions for the accountant app."""
import logging
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accountant_app.service import profile_identifier

logger = logging.getLogger(__name__)


def _get_fine_or_404(fine_id):
    from accountant_app.models import Fine
    try:
        return Fine.objects.select_related("student", "student__user", "issued_by", "issued_by__profile").get(pk=fine_id)
    except Fine.DoesNotExist:
        return None


def create_fine(*, accountant, student_profile, reason, amount, description="", due_date=None, request=None):
    """
    Issue a new fine/charge to a student.
    Returns the created Fine and optionally a checkout_url if payment gateway is active.
    """
    from accountant_app.models import Fine
    from accountant_app.fine_notifications import notify_fine_issued

    amount = Decimal(str(amount))
    fine = Fine(
        student=student_profile,
        issued_by=accountant,
        reason=reason,
        description=description,
        amount=amount,
        due_date=due_date,
    )
    fine.save()
    try:
        from accountant_app.ledger_service import ensure_charge_for_fine

        ensure_charge_for_fine(fine)
    except Exception:
        logger.exception("Failed to post ledger charge for fine_id=%s", fine.pk)

    # Attempt to create a payment link via gateway
    checkout_url = ""
    if request:
        try:
            checkout_url = _create_fine_payment_link(fine=fine, request=request)
            if checkout_url:
                fine.checkout_url = checkout_url
                Fine.objects.filter(pk=fine.pk).update(checkout_url=checkout_url)
        except Exception:
            logger.warning("Could not create fine payment link for fine_id=%s", fine.pk)

    # Notify student
    try:
        notify_fine_issued(fine=fine)
    except Exception:
        logger.exception("Failed to send fine-issued notification for fine_id=%s", fine.pk)

    return fine


def _create_fine_payment_link(*, fine, request):
    """
    Build a DuitNow/ToyyibPay payment link for a fine using the existing gateway infrastructure.
    Returns the checkout URL string or empty string.
    """
    from accountant_app.models import Fine, FinanceGatewayConfig
    from accountant_app.service import _absolute_backend_url, _callback_url, _create_gateway_checkout

    config = FinanceGatewayConfig.objects.filter(pk=1, is_active=True).first()
    if not config:
        return ""

    external_ref = f"FINE-{fine.pk}-{uuid.uuid4().hex[:8].upper()}"
    student_name = fine.student.user.get_full_name().strip() or fine.student.user.username
    student_email = fine.student.user.email or ""
    amount_in_cents = int(fine.amount * 100)

    payload = {
        "userSecretKey": config.secret_key,
        "categoryCode": config.category_code,
        "billName": f"AIU Fine: {fine.reason[:50]}",
        "billDescription": fine.description or fine.reason,
        "billPriceSetting": 1,
        "billPayorInfo": 1,
        "billAmount": amount_in_cents,
        "billReturnUrl": _absolute_backend_url(request, "finance_payment_return"),
        "billCallbackUrl": _callback_url(request, config),
        "billExternalReferenceNo": external_ref,
        "billTo": student_name,
        "billEmail": student_email,
        "billPhone": getattr(fine.student, "phone", None) or "0000000000",
        "merchantName": config.merchant_name,
    }

    try:
        result = _create_gateway_checkout(config, payload)
        checkout_url = result.get("checkout_url", "")
        bill_code = result.get("gateway_reference", "")
        if bill_code:
            Fine.objects.filter(pk=fine.pk).update(gateway_bill_code=bill_code)
        return checkout_url
    except Exception:
        logger.warning("Gateway checkout failed for fine_id=%s", fine.pk)
        return ""


def mark_fine_paid(fine, *, paid_at=None):
    """Mark a fine as paid (called from payment webhook callback)."""
    from accountant_app.models import Fine
    from accountant_app.fine_notifications import notify_fine_paid

    if fine.status == Fine.STATUS_PAID:
        return fine

    with transaction.atomic():
        Fine.objects.filter(pk=fine.pk).update(
            status=Fine.STATUS_PAID,
            paid_at=paid_at or timezone.now(),
        )
        fine.refresh_from_db()
        try:
            from accountant_app.ledger_service import settle_charge_for_fine

            settle_charge_for_fine(fine, actor=fine.student, description=f"Fine payment received: {fine.reason}")
        except Exception:
            logger.exception("Failed to settle ledger charge for paid fine_id=%s", fine.pk)

    try:
        notify_fine_paid(fine=fine)
    except Exception:
        logger.exception("Failed to send fine-paid notification for fine_id=%s", fine.pk)

    return fine


def _mark_fine_overdue(fine):
    """Mark a fine as overdue and report whether this call changed it."""
    from accountant_app.models import Fine
    from accountant_app.fine_notifications import notify_fine_overdue

    if fine.status not in (Fine.STATUS_PENDING,):
        return fine, False

    updated = Fine.objects.filter(pk=fine.pk, status=Fine.STATUS_PENDING).update(
        status=Fine.STATUS_OVERDUE
    )
    fine.refresh_from_db()
    if not updated:
        return fine, False

    try:
        notify_fine_overdue(fine=fine)
    except Exception:
        logger.exception(
            "Failed to send fine-overdue notification for fine_id=%s",
            fine.pk,
        )

    return fine, True


def mark_fine_overdue(fine):
    """Mark a fine as overdue (called by periodic task)."""
    fine, _ = _mark_fine_overdue(fine)
    return fine


def mark_overdue_fines():
    """
    Find all pending fines whose due_date has passed and mark them overdue.
    Returns count of fines updated.
    """
    from accountant_app.models import Fine

    now = timezone.now()
    qs = (
        Fine.objects.select_related("student", "student__user")
        .filter(
            status=Fine.STATUS_PENDING,
            due_date__isnull=False,
            due_date__lt=now,
        )
        .order_by("pk")
    )
    count = 0
    for fine in qs:
        _, changed = _mark_fine_overdue(fine)
        if changed:
            count += 1
    logger.info("Marked %d fine(s) as overdue.", count)
    return count


def deduct_fine_from_meal_allowance(fine_id, *, accountant_profile, note=""):
    """
    Manually mark a fine as deducted from the student's meal allowance.
    This is a manual ledger action; actual bank deduction is done outside the system.
    """
    from accountant_app.models import Fine
    from accountant_app.fine_notifications import notify_fine_deducted

    fine = _get_fine_or_404(fine_id)
    if fine is None:
        raise ValidationError("Fine not found.")
    if fine.status == Fine.STATUS_PAID:
        raise ValidationError("This fine has already been paid online.")
    if fine.status == Fine.STATUS_DEDUCTED:
        raise ValidationError("This fine has already been marked as deducted.")

    with transaction.atomic():
        Fine.objects.filter(pk=fine.pk).update(
            status=Fine.STATUS_DEDUCTED,
            deducted_at=timezone.now(),
            deducted_by=accountant_profile,
            deduction_note=note,
        )
        fine.refresh_from_db()
        try:
            from accountant_app.ledger_service import settle_charge_for_fine
            from accountant_app.models import StudentLedgerEntry

            settle_charge_for_fine(
                fine,
                actor=accountant_profile,
                entry_type=StudentLedgerEntry.ENTRY_PAYMENT,
                description=f"Fine deducted from meal allowance: {fine.reason}",
            )
        except Exception:
            logger.exception("Failed to settle ledger charge for deducted fine_id=%s", fine.pk)

    try:
        notify_fine_deducted(fine=fine)
    except Exception:
        logger.exception("Failed to send fine-deducted notification for fine_id=%s", fine.pk)

    return fine


def fine_payload(fine):
    """Serialise a Fine instance for API responses."""
    student = fine.student
    return {
        "id": fine.pk,
        "reason": fine.reason,
        "description": fine.description,
        "amount": str(fine.amount),
        "currency": fine.currency,
        "status": fine.status,
        "due_date": fine.due_date.isoformat() if fine.due_date else None,
        "checkout_url": fine.checkout_url,
        "paid_at": fine.paid_at.isoformat() if fine.paid_at else None,
        "deducted_at": fine.deducted_at.isoformat() if fine.deducted_at else None,
        "deduction_note": fine.deduction_note,
        "created_at": fine.created_at.isoformat(),
        "student": {
            "id": student.pk,
            "name": student.user.get_full_name().strip() or student.user.username,
            "email": student.user.email,
            "identifier": profile_identifier(student),
        },
        "issued_by": (
            {
                "id": fine.issued_by.pk,
                "name": fine.issued_by.profile.user.get_full_name().strip() or fine.issued_by.profile.user.username,
            }
            if fine.issued_by
            else None
        ),
    }


def list_fines_for_accountant(*, status_filter=None, student_id=None):
    """Return queryset of fines with optional filters."""
    from accountant_app.models import Fine

    qs = Fine.objects.select_related("student", "student__user", "issued_by", "issued_by__profile", "issued_by__profile__user")
    if status_filter:
        qs = qs.filter(status=status_filter)
    if student_id:
        qs = qs.filter(student_id=student_id)
    return qs


def list_fines_for_student(student_profile):
    """Return queryset of fines for a specific student."""
    from accountant_app.models import Fine

    return Fine.objects.filter(student=student_profile).select_related(
        "student", "student__user", "issued_by", "issued_by__profile", "issued_by__profile__user"
    )
