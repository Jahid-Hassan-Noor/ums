from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, DecimalField, Q, Sum, Value, When
from django.utils import timezone

from admin_app.models import Profile, SystemSetting
from admin_app.settings_registry import (
    SETTINGS_SECTIONS,
    all_settings,
    canteen_policy_settings,
    dining_label as configured_dining_label,
    feature_enabled,
    format_currency_amount,
    institution_timezone,
    invalidate_settings_cache,
    setting_key,
    validate_section_values,
)
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


def _csv_items(value, *, upper=False):
    items = [item.strip() for item in str(value or "").split(",") if item.strip()]
    if upper:
        items = [item.upper() for item in items]
    else:
        items = [item.lower() for item in items]
    return tuple(dict.fromkeys(items))


def dining_label():
    return configured_dining_label()


def canteen_module_enabled():
    return feature_enabled("canteen")


def module_unavailable_message():
    return f"{dining_label()} module is currently unavailable."


def ensure_module_enabled():
    if not canteen_module_enabled():
        raise ValidationError(module_unavailable_message())


def _policy():
    return canteen_policy_settings()


def _explicit_policy_configured():
    return SystemSetting.objects.filter(key=setting_key("canteen_policy")).exists()


def _policy_timezone(policy_values):
    timezone_name = str(policy_values.get("allowance_reset_timezone") or "").strip()
    if timezone_name:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            pass
    return institution_timezone()


def monthly_allowance_amount():
    if not _explicit_policy_configured():
        return setting().monthly_allowance
    try:
        return Decimal(str(_policy().get("monthly_allowance_amount")))
    except Exception:
        return setting().monthly_allowance


def policy_payload():
    policy_values = _policy()
    return {
        **policy_values,
        "enabled": canteen_module_enabled(),
        "label": dining_label(),
        "monthly_allowance_amount": str(monthly_allowance_amount()),
    }


def update_monthly_allowance(amount, updated_by):
    current_sections = all_settings()
    normalized = validate_section_values(
        "canteen_policy",
        {"monthly_allowance_amount": str(amount)},
        current_sections["canteen_policy"],
    )
    SystemSetting.objects.update_or_create(
        key=setting_key("canteen_policy"),
        defaults={
            "value": normalized,
            "description": SETTINGS_SECTIONS["canteen_policy"]["description"],
            "updated_by": updated_by,
        },
    )
    invalidate_settings_cache()
    return Decimal(str(normalized["monthly_allowance_amount"]))


def allowance_month(now=None):
    policy_values = _policy()
    zone = _policy_timezone(policy_values)
    local_now = (now or timezone.now()).astimezone(zone)
    reset_day = int(policy_values.get("allowance_reset_day") or 1)
    reset_hour = int(policy_values.get("allowance_reset_hour") or 0)
    boundary = datetime.combine(
        local_now.date().replace(day=reset_day),
        time(hour=reset_hour),
        tzinfo=local_now.tzinfo,
    )
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
    if not canteen_module_enabled():
        return Profile.objects.none()
    policy_values = _policy()
    students = Profile.objects.select_related("user", "student_detail").filter(
        role=Profile.ROLE_STUDENT,
        is_active=True,
        user__is_active=True,
        student_detail__is_active=True,
    )
    eligible_statuses = _csv_items(policy_values.get("eligible_enrollment_statuses"))
    ineligible_markers = _csv_items(
        policy_values.get("ineligible_enrollment_status_markers")
        or ",".join(INACTIVE_STATUS_MARKERS)
    )
    for marker in ineligible_markers:
        students = students.exclude(student_detail__enrollment_status__icontains=marker)
    if eligible_statuses:
        status_query = Q()
        for status in eligible_statuses:
            status_query |= Q(student_detail__enrollment_status__iexact=status)
        students = students.filter(status_query)
    program_codes = _csv_items(policy_values.get("eligible_program_codes"), upper=True)
    if program_codes:
        students = students.filter(student_detail__program__code__in=program_codes)
    if policy_values.get("require_scholarship") or _csv_items(policy_values.get("eligible_cohort_codes"), upper=True):
        eligible_ids = [
            student.id
            for student in students.select_related("student_detail__program")
            if student_is_eligible(student, policy_values)
        ]
        students = students.filter(id__in=eligible_ids)
    return students


def _student_has_scholarship(detail):
    for attr in (
        "has_scholarship",
        "scholarship_active",
        "scholarship_approved",
        "scholarship_requested",
    ):
        value = getattr(detail, attr, None)
        if isinstance(value, bool):
            return value
    scholarship = getattr(detail, "scholarship", None)
    status = str(getattr(scholarship, "status", scholarship) or "").strip().lower()
    return status in {"active", "approved", "awarded", "granted", "yes", "true"}


def _student_cohort_code(detail):
    for attr in ("cohort", "cohort_code"):
        value = getattr(detail, attr, "")
        if value:
            return str(value).strip().upper()
    return ""


def student_is_eligible(student, policy_values=None):
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
    policy_values = policy_values or _policy()
    eligible_statuses = _csv_items(policy_values.get("eligible_enrollment_statuses"))
    ineligible_markers = _csv_items(
        policy_values.get("ineligible_enrollment_status_markers")
        or ",".join(INACTIVE_STATUS_MARKERS)
    )
    if not detail.is_active:
        return False
    if eligible_statuses and status not in eligible_statuses:
        return False
    if any(marker in status for marker in ineligible_markers):
        return False
    program_codes = _csv_items(policy_values.get("eligible_program_codes"), upper=True)
    if program_codes:
        program = getattr(detail, "program", None)
        program_code = str(getattr(program, "code", "") or "").strip().upper()
        if program_code not in program_codes:
            return False
    cohort_codes = _csv_items(policy_values.get("eligible_cohort_codes"), upper=True)
    if cohort_codes and _student_cohort_code(detail) not in cohort_codes:
        return False
    if policy_values.get("require_scholarship") and not _student_has_scholarship(detail):
        return False
    return True


def setting():
    return CanteenSetting.objects.get_or_create(pk=1)[0]


def allocation_for_month(month):
    month = normalize_month(month)
    bonus = CanteenMonthlyBonus.objects.filter(month=month).values_list("extra_amount", flat=True).first()
    return monthly_allowance_amount() + (bonus or Decimal("0.00"))


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
    if not _policy().get("sync_balance_to_student_profile", True):
        return balance
    Student.objects.filter(profile_id=account.student_id).update(
        canteen_balance=balance,
        updated_at=timezone.now(),
    )
    return balance


def ensure_account(student, month=None):
    ensure_module_enabled()
    if not student_is_eligible(student):
        raise ValidationError(f"This student is not active or is currently ineligible for {dining_label().lower()} allowance.")
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
    if not canteen_module_enabled():
        return {"month": allowance_month(), "created": 0, "updated": 0, "skipped": "disabled"}
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

    if _policy().get("sync_balance_to_student_profile", True):
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
        raise ValidationError({"amount": f"Insufficient balance. Current balance is {format_currency_amount(account.balance)}."})
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
    if not canteen_module_enabled():
        return {
            "enabled": False,
            "message": module_unavailable_message(),
            "month": month.isoformat(),
            "eligible_students": 0,
            "monthly_allowance": str(monthly_allowance_amount()),
            "extra_amount": "0.00",
            "allocated": "0.00",
            "manual_additions": "0.00",
            "spent": "0.00",
            "transactions": 0,
            "policy": policy_payload(),
        }
    initialize_accounts(month)
    accounts = StudentCanteenAccount.objects.filter(month=month)
    totals = accounts.aggregate(spent=Sum("spent_amount"), allowance=Sum("allowance_amount"))
    adjustments = CanteenBalanceAdjustment.objects.filter(account__month=month).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")
    return {
        "month": month.isoformat(),
        "enabled": True,
        "eligible_students": accounts.count(),
        "monthly_allowance": str(monthly_allowance_amount()),
        "extra_amount": str(
            CanteenMonthlyBonus.objects.filter(month=month).values_list("extra_amount", flat=True).first()
            or Decimal("0.00")
        ),
        "allocated": str(totals["allowance"] or Decimal("0.00")),
        "manual_additions": str(adjustments),
        "spent": str(totals["spent"] or Decimal("0.00")),
        "transactions": CanteenTransaction.objects.filter(account__month=month).count(),
        "policy": policy_payload(),
    }
