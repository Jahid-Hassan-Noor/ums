from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from accountant_app.models import (
    FeeCategory,
    PaymentPlan,
    PaymentPlanInstallment,
    StudentBalanceSnapshot,
    StudentCharge,
    StudentFinanceHold,
    StudentLedgerEntry,
)
from accountant_app.service import display_name, money, profile_identifier
from admin_app.models import Profile
from admin_app.settings_registry import default_currency_code, format_currency_amount
from core.common.pagination import paginate


BALANCE_INCREASE_TYPES = {
    StudentLedgerEntry.ENTRY_DEBIT,
    StudentLedgerEntry.ENTRY_REFUND,
    StudentLedgerEntry.ENTRY_ADJUSTMENT,
}
BALANCE_DECREASE_TYPES = {
    StudentLedgerEntry.ENTRY_PAYMENT,
    StudentLedgerEntry.ENTRY_WAIVER,
    StudentLedgerEntry.ENTRY_REVERSAL,
}


def _decimal(value, field_name="amount"):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({field_name: "Enter a valid amount."}) from exc
    if amount <= 0:
        raise ValidationError({field_name: "Amount must be greater than zero."})
    return amount


def _student_or_error(student_id):
    student = Profile.objects.select_related("user").filter(pk=student_id, role=Profile.ROLE_STUDENT).first()
    if not student:
        raise ValidationError({"student_id": "Student not found."})
    return student


def _currency_code(value=None):
    code = str(value or default_currency_code()).strip().upper()
    return code if len(code) == 3 and code.isalpha() else default_currency_code()


def _money_label(amount, currency=None):
    return format_currency_amount(amount, currency_code=_currency_code(currency))


def student_payload(profile):
    return {
        "id": profile.id,
        "name": display_name(profile),
        "email": profile.user.email,
        "identifier": profile_identifier(profile),
    }


def category_payload(category):
    return {
        "id": category.id,
        "code": category.code,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active,
    }


def charge_payload(charge):
    return {
        "id": charge.id,
        "student": student_payload(charge.student),
        "category": category_payload(charge.category),
        "source_type": charge.source_type,
        "source_id": charge.source_id,
        "description": charge.description,
        "amount": money(charge.amount),
        "amount_display": _money_label(charge.amount, charge.currency),
        "currency": charge.currency,
        "due_date": charge.due_date.isoformat() if charge.due_date else None,
        "status": charge.status,
        "created_at": charge.created_at.isoformat(),
    }


def ledger_entry_payload(entry):
    return {
        "id": entry.id,
        "student": student_payload(entry.student),
        "charge_id": entry.charge_id,
        "entry_type": entry.entry_type,
        "amount": money(entry.amount),
        "amount_display": _money_label(entry.amount, entry.currency),
        "currency": entry.currency,
        "description": entry.description,
        "balance_after": money(entry.balance_after),
        "balance_after_display": _money_label(entry.balance_after, entry.currency),
        "posted_at": entry.posted_at.isoformat(),
        "posted_by": display_name(entry.posted_by) if entry.posted_by_id else "",
    }


def hold_payload(hold):
    return {
        "id": hold.id,
        "student": student_payload(hold.student),
        "reason": hold.reason,
        "notes": hold.notes,
        "is_active": hold.is_active,
        "placed_at": hold.placed_at.isoformat(),
        "released_at": hold.released_at.isoformat() if hold.released_at else None,
    }


def current_balance_for_student(student):
    try:
        snapshot = student.student_finance_balance
        return snapshot.balance
    except StudentBalanceSnapshot.DoesNotExist:
        pass
    debit_total = StudentLedgerEntry.objects.filter(
        student=student,
        entry_type__in=BALANCE_INCREASE_TYPES,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    credit_total = StudentLedgerEntry.objects.filter(
        student=student,
        entry_type__in=BALANCE_DECREASE_TYPES,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return debit_total - credit_total


def sync_balance_snapshot(student, balance, currency=None):
    StudentBalanceSnapshot.objects.update_or_create(
        student=student,
        defaults={"balance": balance, "currency": _currency_code(currency)},
    )


@transaction.atomic
def record_ledger_entry(*, student, entry_type, amount, description, actor=None, charge=None, currency=None):
    amount = _decimal(amount)
    entry_currency = _currency_code(currency or getattr(charge, "currency", None))
    if entry_type not in BALANCE_INCREASE_TYPES | BALANCE_DECREASE_TYPES:
        raise ValidationError({"entry_type": "Unsupported ledger entry type."})

    StudentLedgerEntry.objects.select_for_update().filter(student=student).order_by("pk").last()
    current_balance = current_balance_for_student(student)
    if entry_type in BALANCE_INCREASE_TYPES:
        balance_after = current_balance + amount
    else:
        balance_after = current_balance - amount

    entry = StudentLedgerEntry.objects.create(
        student=student,
        charge=charge,
        entry_type=entry_type,
        amount=amount,
        currency=entry_currency,
        description=description,
        balance_after=balance_after,
        posted_by=actor,
    )
    sync_balance_snapshot(student, balance_after, entry_currency)
    return entry


def get_or_create_category(*, code, name=None):
    code = str(code or "").strip().upper()
    if not code:
        raise ValidationError({"category": "Fee category is required."})
    category, _created = FeeCategory.objects.get_or_create(
        code=code,
        defaults={"name": name or code.replace("_", " ").title()},
    )
    return category


@transaction.atomic
def create_fee_category(*, data):
    category_id = data.get("category_id") or data.get("id")
    category = FeeCategory.objects.filter(pk=category_id).first() if category_id else None
    if category is None:
        category = FeeCategory()
    category.code = str(data.get("code") or category.code).strip().upper()
    category.name = str(data.get("name") or category.name).strip()
    category.description = str(data.get("description") or "").strip()
    if "is_active" in data:
        category.is_active = bool(data.get("is_active"))
    category.save()
    return category


@transaction.atomic
def create_student_charge(*, actor, data):
    student = _student_or_error(data.get("student_id"))
    category = None
    if data.get("category_id"):
        category = FeeCategory.objects.filter(pk=data.get("category_id"), is_active=True).first()
    if category is None:
        category = get_or_create_category(
            code=data.get("category_code") or data.get("source_type") or StudentCharge.SOURCE_MANUAL,
            name=data.get("category_name"),
        )
    amount = _decimal(data.get("amount"))
    currency = _currency_code(data.get("currency"))
    description = str(data.get("description") or category.name).strip()
    if not description:
        raise ValidationError({"description": "Charge description is required."})

    charge = StudentCharge.objects.create(
        student=student,
        category=category,
        source_type=data.get("source_type") or StudentCharge.SOURCE_MANUAL,
        source_id=data.get("source_id") or None,
        description=description,
        amount=amount,
        currency=currency,
        due_date=data.get("due_date") or None,
        issued_by=actor,
    )
    record_ledger_entry(
        student=student,
        charge=charge,
        entry_type=StudentLedgerEntry.ENTRY_DEBIT,
        amount=amount,
        description=description,
        actor=actor,
        currency=currency,
    )
    return charge


@transaction.atomic
def record_student_payment(*, actor, data):
    student = _student_or_error(data.get("student_id"))
    description = str(data.get("description") or "Manual payment recorded").strip()
    if not description:
        raise ValidationError({"description": "Payment description is required."})
    return record_ledger_entry(
        student=student,
        entry_type=StudentLedgerEntry.ENTRY_PAYMENT,
        amount=data.get("amount"),
        description=description,
        actor=actor,
        currency=data.get("currency"),
    )


def ensure_charge_for_fine(fine):
    category = get_or_create_category(code="FINE", name="Student fines")
    charge, created = StudentCharge.objects.get_or_create(
        source_type=StudentCharge.SOURCE_FINE,
        source_id=fine.pk,
        defaults={
            "student": fine.student,
            "category": category,
            "description": fine.reason,
            "amount": fine.amount,
            "currency": _currency_code(fine.currency),
            "due_date": fine.due_date.date() if fine.due_date else None,
            "issued_by": fine.issued_by.profile if fine.issued_by_id else None,
        },
    )
    if created:
        record_ledger_entry(
            student=fine.student,
            charge=charge,
            entry_type=StudentLedgerEntry.ENTRY_DEBIT,
            amount=fine.amount,
            description=f"Fine issued: {fine.reason}",
            actor=fine.issued_by.profile if fine.issued_by_id else None,
            currency=fine.currency,
        )
    return charge


def settle_charge_for_fine(fine, *, actor=None, entry_type=StudentLedgerEntry.ENTRY_PAYMENT, description=None):
    charge = StudentCharge.objects.filter(source_type=StudentCharge.SOURCE_FINE, source_id=fine.pk).first()
    if not charge:
        charge = ensure_charge_for_fine(fine)
    existing = StudentLedgerEntry.objects.filter(
        charge=charge,
        entry_type__in={StudentLedgerEntry.ENTRY_PAYMENT, StudentLedgerEntry.ENTRY_WAIVER, StudentLedgerEntry.ENTRY_REVERSAL},
    ).exists()
    if existing:
        return None
    return record_ledger_entry(
        student=fine.student,
        charge=charge,
        entry_type=entry_type,
        amount=fine.amount,
        description=description or f"Fine settled: {fine.reason}",
        actor=actor,
    )


def student_finance_summary(student):
    balance = current_balance_for_student(student)
    snapshot = StudentBalanceSnapshot.objects.filter(student=student).first()
    currency = _currency_code(snapshot.currency if snapshot else None)
    holds = StudentFinanceHold.objects.filter(student=student, is_active=True)
    charges = StudentCharge.objects.select_related("category", "student", "student__user").filter(student=student)
    entries = StudentLedgerEntry.objects.select_related("student", "student__user", "posted_by", "posted_by__user").filter(student=student)
    return {
        "student": student_payload(student),
        "balance": money(balance),
        "balance_display": _money_label(balance, currency),
        "currency": currency,
        "active_holds": [hold_payload(hold) for hold in holds],
        "charges": [charge_payload(charge) for charge in charges[:100]],
        "ledger_entries": [ledger_entry_payload(entry) for entry in entries[:200]],
    }


def student_balance_summaries(*, query=None):
    students = Profile.objects.select_related("user").filter(role=Profile.ROLE_STUDENT)
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(student_detail__student_id__icontains=query)
        )
    rows = []
    for student in students[:200]:
        snapshot = StudentBalanceSnapshot.objects.filter(student=student).first()
        balance = snapshot.balance if snapshot else current_balance_for_student(student)
        currency = _currency_code(snapshot.currency if snapshot else None)
        rows.append({
            "student": student_payload(student),
            "balance": money(balance),
            "balance_display": _money_label(balance, currency),
            "currency": currency,
            "active_holds": StudentFinanceHold.objects.filter(student=student, is_active=True).count(),
        })
    return rows


@transaction.atomic
def place_finance_hold(*, actor, data):
    student = _student_or_error(data.get("student_id"))
    reason = str(data.get("reason") or "").strip()
    if not reason:
        raise ValidationError({"reason": "Hold reason is required."})
    return StudentFinanceHold.objects.create(
        student=student,
        reason=reason,
        notes=str(data.get("notes") or "").strip(),
        placed_by=actor,
    )


@transaction.atomic
def release_finance_hold(*, actor, hold_id):
    hold = StudentFinanceHold.objects.select_for_update().filter(pk=hold_id).first()
    if not hold:
        raise ValidationError("Finance hold not found.")
    if hold.is_active:
        hold.is_active = False
        hold.released_by = actor
        hold.released_at = timezone.now()
        hold.save(update_fields=["is_active", "released_by", "released_at"])
    return hold


def payment_plan_payload(plan):
    installments = plan.installments.all()
    paid_count = installments.filter(status=PaymentPlanInstallment.STATUS_PAID).count()
    return {
        "id": plan.id,
        "student": student_payload(plan.student),
        "charge_id": plan.charge_id,
        "description": plan.description,
        "total_amount": money(plan.total_amount),
        "total_amount_display": _money_label(plan.total_amount, plan.currency),
        "currency": plan.currency,
        "installment_count": plan.installment_count,
        "frequency": plan.frequency,
        "status": plan.status,
        "paid_installments": paid_count,
        "remaining_installments": plan.installment_count - paid_count,
        "created_at": plan.created_at.isoformat(),
        "installments": [installment_payload(inst) for inst in installments],
    }


def installment_payload(installment):
    return {
        "id": installment.id,
        "installment_number": installment.installment_number,
        "amount": money(installment.amount),
        "amount_display": _money_label(installment.amount, installment.plan.currency),
        "due_date": installment.due_date.isoformat(),
        "status": installment.status,
        "paid_at": installment.paid_at.isoformat() if installment.paid_at else None,
        "ledger_entry_id": installment.ledger_entry_id,
        "notes": installment.notes,
    }


def dashboard_summary():
    total_students = Profile.objects.filter(role=Profile.ROLE_STUDENT).count()
    students_with_balance = StudentBalanceSnapshot.objects.filter(balance__gt=0).count()
    total_outstanding = StudentBalanceSnapshot.objects.aggregate(total=Sum("balance"))["total"] or Decimal("0.00")
    active_holds = StudentFinanceHold.objects.filter(is_active=True).count()
    total_charges = StudentCharge.objects.count()
    total_charges_amount = StudentCharge.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_entries = StudentLedgerEntry.objects.count()
    total_payments = StudentLedgerEntry.objects.filter(entry_type=StudentLedgerEntry.ENTRY_PAYMENT).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    overdue_charges = StudentCharge.objects.filter(
        due_date__lt=timezone.now().date(),
        status=StudentCharge.STATUS_POSTED,
    ).count()
    active_plans = PaymentPlan.objects.filter(status=PaymentPlan.STATUS_ACTIVE).count()

    category_breakdown = (
        StudentCharge.objects.filter(status=StudentCharge.STATUS_POSTED)
        .values("category__code", "category__name")
        .annotate(total=Sum("amount"), count=models.Count("id"))
        .order_by("-total")
    )

    return {
        "currency": default_currency_code(),
        "total_students": total_students,
        "students_with_balance": students_with_balance,
        "total_outstanding": money(total_outstanding),
        "total_outstanding_display": _money_label(total_outstanding),
        "active_holds": active_holds,
        "total_charges": total_charges,
        "total_charges_amount": money(total_charges_amount),
        "total_entries": total_entries,
        "total_payments": money(total_payments),
        "overdue_charges": overdue_charges,
        "active_plans": active_plans,
        "category_breakdown": [
            {
                "code": row["category__code"],
                "name": row["category__name"],
                "total": money(row["total"]),
                "total_display": _money_label(row["total"]),
                "count": row["count"],
            }
            for row in category_breakdown
        ],
    }


def student_balance_summaries_paginated(*, query=None, sort_by=None, page=1, page_size=20):
    students = Profile.objects.select_related("user").filter(role=Profile.ROLE_STUDENT)
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(student_detail__student_id__icontains=query)
        )

    rows = []
    for student in students:
        snapshot = StudentBalanceSnapshot.objects.filter(student=student).first()
        balance = snapshot.balance if snapshot else current_balance_for_student(student)
        currency = _currency_code(snapshot.currency if snapshot else None)
        holds_count = StudentFinanceHold.objects.filter(student=student, is_active=True).count()
        last_entry = StudentLedgerEntry.objects.filter(student=student).order_by("-posted_at").first()
        rows.append({
            "student": student_payload(student),
            "balance": money(balance),
            "balance_display": _money_label(balance, currency),
            "currency": currency,
            "balance_raw": balance,
            "active_holds": holds_count,
            "last_activity": last_entry.posted_at.isoformat() if last_entry else None,
        })

    if sort_by == "balance_desc":
        rows.sort(key=lambda r: r["balance_raw"], reverse=True)
    elif sort_by == "balance_asc":
        rows.sort(key=lambda r: r["balance_raw"])
    elif sort_by == "name":
        rows.sort(key=lambda r: r["student"]["name"])
    elif sort_by == "holds":
        rows.sort(key=lambda r: r["active_holds"], reverse=True)

    for row in rows:
        row.pop("balance_raw", None)

    page_rows, meta = paginate(rows, page=page, page_size=page_size)
    return {
        "students": page_rows,
        **meta,
    }


def audit_trail(*, query=None, entry_type=None, student_id=None, date_from=None, date_to=None, page=1, page_size=50):
    entries = StudentLedgerEntry.objects.select_related("student", "student__user", "posted_by", "posted_by__user")

    if student_id:
        entries = entries.filter(student_id=student_id)
    if entry_type:
        entries = entries.filter(entry_type=entry_type)
    if query:
        entries = entries.filter(
            Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(description__icontains=query)
        )
    if date_from:
        entries = entries.filter(posted_at__date__gte=date_from)
    if date_to:
        entries = entries.filter(posted_at__date__lte=date_to)

    entries = entries.order_by("-posted_at", "-id")
    page_entries, meta = paginate(entries, page=page, page_size=page_size)

    return {
        "entries": [ledger_entry_payload(entry) for entry in page_entries],
        **meta,
    }


@transaction.atomic
def create_bulk_charge(*, actor, data):
    category_id = data.get("category_id")
    student_ids = data.get("student_ids", [])
    amount = _decimal(data.get("amount"))
    currency = _currency_code(data.get("currency"))
    description = str(data.get("description") or "").strip()
    due_date = data.get("due_date") or None

    if not student_ids:
        raise ValidationError({"student_ids": "Select at least one student."})
    if not description:
        raise ValidationError({"description": "Charge description is required."})

    category = None
    if category_id:
        category = FeeCategory.objects.filter(pk=category_id, is_active=True).first()
    if category is None:
        category = get_or_create_category(
            code=data.get("category_code") or StudentCharge.SOURCE_MANUAL,
            name=data.get("category_name"),
        )

    charges = []
    errors = []
    for sid in student_ids:
        try:
            student = _student_or_error(sid)
            charge = StudentCharge.objects.create(
                student=student,
                category=category,
                source_type=StudentCharge.SOURCE_MANUAL,
                description=description,
                amount=amount,
                currency=currency,
                due_date=due_date,
                issued_by=actor,
            )
            record_ledger_entry(
                student=student,
                charge=charge,
                entry_type=StudentLedgerEntry.ENTRY_DEBIT,
                amount=amount,
                description=description,
                actor=actor,
                currency=currency,
            )
            charges.append(charge_payload(charge))
        except (ValidationError, Exception) as exc:
            errors.append({"student_id": sid, "error": str(exc)})

    return {"charges": charges, "errors": errors, "posted_count": len(charges), "error_count": len(errors)}


@transaction.atomic
def create_payment_plan(*, actor, data):
    student = _student_or_error(data.get("student_id"))
    total_amount = _decimal(data.get("total_amount"))
    currency = _currency_code(data.get("currency"))
    installment_count = int(data.get("installment_count", 2))
    frequency = data.get("frequency", PaymentPlan.FREQUENCY_MONTHLY)
    description = str(data.get("description") or "").strip()
    charge_id = data.get("charge_id")

    if installment_count < 2:
        raise ValidationError({"installment_count": "Must have at least 2 installments."})

    charge = None
    if charge_id:
        charge = StudentCharge.objects.filter(pk=charge_id, student=student).first()

    plan = PaymentPlan.objects.create(
        student=student,
        charge=charge,
        description=description or f"Payment plan for {student.user.get_full_name() or student.user.username}",
        total_amount=total_amount,
        currency=currency,
        installment_count=installment_count,
        frequency=frequency,
        created_by=actor,
    )

    installment_amount = total_amount / installment_count
    today = timezone.now().date()

    for i in range(1, installment_count + 1):
        if frequency == PaymentPlan.FREQUENCY_WEEKLY:
            due = today + timezone.timedelta(weeks=i)
        elif frequency == PaymentPlan.FREQUENCY_BIWEEKLY:
            due = today + timezone.timedelta(weeks=i * 2)
        else:
            due = today + timezone.timedelta(days=30 * i)

        PaymentPlanInstallment.objects.create(
            plan=plan,
            installment_number=i,
            amount=installment_amount,
            due_date=due,
        )

    return plan


@transaction.atomic
def record_plan_payment(*, actor, plan_id, data):
    plan = PaymentPlan.objects.select_for_update().filter(pk=plan_id).first()
    if not plan:
        raise ValidationError({"plan_id": "Payment plan not found."})
    if plan.status != PaymentPlan.STATUS_ACTIVE:
        raise ValidationError({"plan_id": "This payment plan is no longer active."})

    installment_id = data.get("installment_id")
    installment = PaymentPlanInstallment.objects.filter(
        pk=installment_id, plan=plan, status=PaymentPlanInstallment.STATUS_PENDING
    ).first()
    if not installment:
        raise ValidationError({"installment_id": "Invalid or already paid installment."})

    entry = record_ledger_entry(
        student=plan.student,
        charge=plan.charge,
        entry_type=StudentLedgerEntry.ENTRY_PAYMENT,
        amount=installment.amount,
        description=f"Payment plan installment #{installment.installment_number} for: {plan.description}",
        actor=actor,
        currency=plan.currency,
    )

    installment.status = PaymentPlanInstallment.STATUS_PAID
    installment.paid_at = timezone.now()
    installment.ledger_entry = entry
    installment.save(update_fields=["status", "paid_at", "ledger_entry"])

    all_paid = not PaymentPlanInstallment.objects.filter(plan=plan, status=PaymentPlanInstallment.STATUS_PENDING).exists()
    if all_paid:
        plan.status = PaymentPlan.STATUS_COMPLETED
        plan.save(update_fields=["status"])

    return plan


def student_ledger_entries(*, student_id, page=1, page_size=20, entry_type=None, date_from=None, date_to=None):
    entries = StudentLedgerEntry.objects.select_related("charge", "posted_by", "posted_by__user").filter(student_id=student_id)
    if entry_type:
        entries = entries.filter(entry_type=entry_type)
    if date_from:
        entries = entries.filter(posted_at__date__gte=date_from)
    if date_to:
        entries = entries.filter(posted_at__date__lte=date_to)

    entries = entries.order_by("-posted_at", "-id")
    page_entries, meta = paginate(entries, page=page, page_size=page_size)

    return {
        "entries": [ledger_entry_payload(entry) for entry in page_entries],
        **meta,
    }


def student_charges_filtered(*, student_id, page=1, page_size=20, status=None, category_id=None, date_from=None, date_to=None):
    charges = StudentCharge.objects.select_related("category").filter(student_id=student_id)
    if status:
        charges = charges.filter(status=status)
    if category_id:
        charges = charges.filter(category_id=category_id)
    if date_from:
        charges = charges.filter(created_at__date__gte=date_from)
    if date_to:
        charges = charges.filter(created_at__date__lte=date_to)

    charges = charges.order_by("-created_at")
    page_charges, meta = paginate(charges, page=page, page_size=page_size)

    return {
        "charges": [charge_payload(charge) for charge in page_charges],
        **meta,
    }


def holds_filtered(*, query=None, is_active=None, page=1, page_size=20):
    holds = StudentFinanceHold.objects.select_related("student", "student__user", "placed_by", "placed_by__user", "released_by", "released_by__user")
    if is_active is not None:
        holds = holds.filter(is_active=is_active)
    if query:
        holds = holds.filter(
            Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(reason__icontains=query)
        )

    holds = holds.order_by("-placed_at")
    page_holds, meta = paginate(holds, page=page, page_size=page_size)

    return {
        "holds": [hold_payload(hold) for hold in page_holds],
        **meta,
    }
