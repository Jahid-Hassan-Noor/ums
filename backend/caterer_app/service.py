from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, DecimalField, Q, Sum, Value, When
from django.utils import timezone

from admin_app.models import Profile
from caterer_app.models import (
    CanteenBalanceAdjustment,
    CanteenMonthlyBonus,
    CanteenSetting,
    CanteenTransaction,
    StudentCanteenAccount,
)
from core.common.profiles import (
    profile_display_name as student_name,
    profile_identifier as student_identifier,
)
from student_app.models import Student


INACTIVE_STATUS_MARKERS = (
    "terminated",
    "graduat",
    "dropout",
    "drop out",
    "withdraw",
    "internship",
)
CANTEEN_TIME_ZONE = ZoneInfo("Asia/Kuala_Lumpur")


def allowance_month(now=None):
    local_now = (now or timezone.now()).astimezone(CANTEEN_TIME_ZONE)
    boundary = datetime.combine(local_now.date().replace(day=1), time(hour=8), tzinfo=local_now.tzinfo)
    if local_now < boundary:
        previous_day = local_now.date().replace(day=1) - timedelta(days=1)
        return previous_day.replace(day=1)
    return local_now.date().replace(day=1)


def normalize_month(value):
    if isinstance(value, date):
        return value.replace(day=1)
    try:
        parsed = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValidationError({"month": "Provide a valid month in YYYY-MM-DD format."})
    return parsed.replace(day=1)


def active_students():
    students = Profile.objects.select_related("user", "student_detail").filter(
        role=Profile.ROLE_STUDENT,
        is_active=True,
        user__is_active=True,
        student_detail__is_active=True,
    )
    for marker in INACTIVE_STATUS_MARKERS:
        students = students.exclude(student_detail__enrollment_status__icontains=marker)
    return students.exclude(student_detail__enrollment_status__iexact="intern")


def student_is_eligible(student):
    if (
        student.role != Profile.ROLE_STUDENT
        or not student.is_active
        or not student.user.is_active
    ):
        return False
    try:
        detail = student.student_detail
    except Exception:
        return False
    status = str(detail.enrollment_status or "").strip().lower()
    return detail.is_active and status != "intern" and not any(
        marker in status for marker in INACTIVE_STATUS_MARKERS
    )


def setting():
    return CanteenSetting.objects.get_or_create(pk=1)[0]


def allocation_for_month(month):
    month = normalize_month(month)
    bonus = CanteenMonthlyBonus.objects.filter(month=month).values_list("extra_amount", flat=True).first()
    return setting().monthly_allowance + (bonus or Decimal("0.00"))


def find_student(identifier):
    identifier = str(identifier or "").strip()
    if not identifier:
        return None
    return (
        Profile.objects.select_related("user", "student_detail")
        .filter(role=Profile.ROLE_STUDENT)
        .filter(
            Q(student_detail__student_id__iexact=identifier)
            | Q(user__username__iexact=identifier)
        )
        .first()
    )


def sync_student_balance(account):
    balance = account.balance
    Student.objects.filter(profile_id=account.student_id).update(
        canteen_balance=balance,
        updated_at=timezone.now(),
    )
    return balance


def ensure_account(student, month=None):
    if not student_is_eligible(student):
        raise ValidationError("This student is not active or is currently ineligible for canteen allowance.")
    month = normalize_month(month or allowance_month())
    allocation = allocation_for_month(month)
    account, created = StudentCanteenAccount.objects.get_or_create(
        student=student,
        month=month,
        defaults={"allowance_amount": allocation},
    )
    if not created and account.allowance_amount != allocation:
        account.allowance_amount = allocation
        account.save(update_fields=["allowance_amount", "updated_at"])
    sync_student_balance(account)
    return account


def initialize_accounts(month=None):
    month = normalize_month(month or allowance_month())
    allocation = allocation_for_month(month)
    student_ids = list(active_students().values_list("id", flat=True))
    existing_accounts = StudentCanteenAccount.objects.filter(
        month=month,
        student_id__in=student_ids,
    )
    existing_student_ids = set(existing_accounts.values_list("student_id", flat=True))
    updated = existing_accounts.exclude(allowance_amount=allocation).update(
        allowance_amount=allocation,
        updated_at=timezone.now(),
    )
    new_accounts = [
        StudentCanteenAccount(
            student_id=student_id,
            month=month,
            allowance_amount=allocation,
        )
        for student_id in student_ids
        if student_id not in existing_student_ids
    ]
    StudentCanteenAccount.objects.bulk_create(new_accounts, batch_size=500, ignore_conflicts=True)

    account_balances = StudentCanteenAccount.objects.filter(
        month=month,
        student_id__in=student_ids,
    ).annotate(
        adjustment_total=Sum("adjustments__amount"),
    ).values("student_id", "allowance_amount", "spent_amount", "adjustment_total")
    now = timezone.now()
    account_balances = list(account_balances)
    for start in range(0, len(account_balances), 500):
        batch = account_balances[start : start + 500]
        Student.objects.filter(profile_id__in=[item["student_id"] for item in batch]).update(
            canteen_balance=Case(
                *[
                    When(
                        profile_id=item["student_id"],
                        then=Value(
                            item["allowance_amount"]
                            + (item["adjustment_total"] or Decimal("0.00"))
                            - item["spent_amount"]
                        ),
                    )
                    for item in batch
                ],
                output_field=DecimalField(max_digits=8, decimal_places=2),
            ),
            updated_at=now,
        )
    Student.objects.exclude(profile_id__in=student_ids).exclude(canteen_balance=Decimal("0.00")).update(
        canteen_balance=Decimal("0.00"),
        updated_at=now,
    )
    return {"month": month, "created": len(new_accounts), "updated": updated}


def transaction_payload(transaction):
    return {
        "id": transaction.id,
        "amount": str(transaction.amount),
        "description": transaction.description,
        "caterer_name": student_name(transaction.caterer),
        "created_at": transaction.created_at.isoformat(),
    }


def adjustment_payload(adjustment):
    return {
        "id": adjustment.id,
        "amount": str(adjustment.amount),
        "reason": adjustment.reason,
        "added_by_name": student_name(adjustment.added_by),
        "created_at": adjustment.created_at.isoformat(),
    }


def account_payload(account):
    student = account.student
    return {
        "student": {
            "id": student.id,
            "student_id": student_identifier(student),
            "name": student_name(student),
            "email": student.user.email,
            "enrollment_status": student.student_detail.enrollment_status,
        },
        "month": account.month.isoformat(),
        "allowance_amount": str(account.allowance_amount),
        "adjustment_amount": str(account.adjustment_amount),
        "spent_amount": str(account.spent_amount),
        "balance": str(account.balance),
        "adjustments": [
            adjustment_payload(item)
            for item in account.adjustments.select_related("added_by__user").all()
        ],
        "transactions": [
            transaction_payload(item)
            for item in account.transactions.select_related("caterer__user").all()
        ],
    }


@transaction.atomic
def deduct(student, caterer, amount, description=""):
    try:
        amount = Decimal(str(amount))
    except Exception:
        raise ValidationError({"amount": "Provide a valid transaction amount."})
    if amount <= 0:
        raise ValidationError({"amount": "Transaction amount must be greater than zero."})

    account = ensure_account(student)
    account = StudentCanteenAccount.objects.select_for_update().get(pk=account.pk)
    if amount > account.balance:
        raise ValidationError({"amount": f"Insufficient balance. Current balance is RM {account.balance:.2f}."})
    transaction_record = CanteenTransaction.objects.create(
        account=account,
        caterer=caterer,
        amount=amount,
        description=str(description or "").strip(),
    )
    account.spent_amount += amount
    account.save(update_fields=["spent_amount", "updated_at"])
    sync_student_balance(account)
    return account, transaction_record


@transaction.atomic
def add_balance(student, admin_profile, amount, reason):
    if admin_profile.role != Profile.ROLE_ACCOUNTANT:
        raise ValidationError("Only accountants can add student canteen balance.")
    try:
        amount = Decimal(str(amount))
    except Exception:
        raise ValidationError({"amount": "Provide a valid balance amount."})
    if amount <= 0:
        raise ValidationError({"amount": "Added balance must be greater than zero."})
    reason = str(reason or "").strip()
    if not reason:
        raise ValidationError({"reason": "A reason is required for manual balance additions."})

    account = ensure_account(student)
    account = StudentCanteenAccount.objects.select_for_update().get(pk=account.pk)
    adjustment = CanteenBalanceAdjustment.objects.create(
        account=account,
        added_by=admin_profile,
        amount=amount,
        reason=reason,
    )
    sync_student_balance(account)
    return account, adjustment


def dashboard_summary():
    month = allowance_month()
    initialize_accounts(month)
    accounts = StudentCanteenAccount.objects.filter(month=month)
    totals = accounts.aggregate(spent=Sum("spent_amount"), allowance=Sum("allowance_amount"))
    adjustments = CanteenBalanceAdjustment.objects.filter(account__month=month).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")
    return {
        "month": month.isoformat(),
        "eligible_students": accounts.count(),
        "monthly_allowance": str(setting().monthly_allowance),
        "extra_amount": str(
            CanteenMonthlyBonus.objects.filter(month=month).values_list("extra_amount", flat=True).first()
            or Decimal("0.00")
        ),
        "allocated": str(totals["allowance"] or Decimal("0.00")),
        "manual_additions": str(adjustments),
        "spent": str(totals["spent"] or Decimal("0.00")),
        "transactions": CanteenTransaction.objects.filter(account__month=month).count(),
    }
