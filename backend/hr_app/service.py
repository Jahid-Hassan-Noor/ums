from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from admin_app.models import Profile
from admin_app.settings_registry import default_currency_code
from core.common.profiles import (
    profile_display_name as display_name,
    profile_identifier,
)
from hr_app.models import (
    CompensationChangeRequest,
    Employee,
    EmployeeDocument,
    EmploymentRecord,
    HRStaff,
    Position,
    SalaryAdjustment,
)


EMPLOYEE_ROLES = {
    Profile.ROLE_TEACHER,
    Profile.ROLE_EXECUTIVE,
    Profile.ROLE_LIBRARIAN,
    Profile.ROLE_CATERER,
    Profile.ROLE_TECHNICIAN,
    Profile.ROLE_ACCOUNTANT,
    Profile.ROLE_HR,
    Profile.ROLE_ADMIN,
}

MONEY_QUANT = Decimal("0.01")


def money_payload(value):
    return str((value or Decimal("0.00")).quantize(MONEY_QUANT))


def _sum_money(value):
    return value or Decimal("0.00")


def _profile_payload(profile):
    if not profile:
        return None
    return {
        "id": profile.id,
        "name": display_name(profile),
        "role": profile.role,
        "identifier": profile_identifier(profile),
        "email": profile.user.email,
    }


def parse_money(value, field, *, allow_zero=True):
    if value in (None, ""):
        return Decimal("0.00")
    try:
        amount = Decimal(str(value)).quantize(MONEY_QUANT)
    except (InvalidOperation, ValueError):
        raise ValidationError({field: "Enter a valid amount."})
    if amount < 0:
        raise ValidationError({field: "Amount cannot be negative."})
    if not allow_zero and amount <= 0:
        raise ValidationError({field: "Amount must be greater than zero."})
    return amount


def position_payload(position):
    return {
        "id": position.id,
        "code": position.code,
        "title": position.title,
        "employment_type": position.employment_type,
        "employment_type_label": position.get_employment_type_display(),
        "grade": position.grade,
        "department": position.department.name if position.department_id else "",
        "unit": position.unit.name if position.unit_id else "",
        "is_active": position.is_active,
    }


def manager_payload(employee):
    if not employee.reporting_manager_id:
        return None
    return {
        "id": employee.reporting_manager_id,
        "name": display_name(employee.reporting_manager.profile),
        "employee_no": employee.reporting_manager.employee_no,
    }


def leave_placeholder_payload():
    return {
        "vacation_days_total": 21,
        "vacation_days_used": 0,
        "vacation_days_remaining": 21,
        "leave_days_total": 14,
        "leave_days_used": 0,
        "leave_days_remaining": 14,
        "is_placeholder": True,
    }


def employee_payload(employee):
    profile = employee.profile
    payload = {
        "id": employee.id,
        "profile_id": profile.id,
        "employee_no": employee.employee_no,
        "name": display_name(profile),
        "email": profile.user.email,
        "role": profile.role,
        "identifier": profile_identifier(profile),
        "employment_status": employee.employment_status,
        "employment_status_label": employee.get_employment_status_display(),
        "joining_date": employee.joining_date.isoformat() if employee.joining_date else None,
        "work_email": employee.work_email,
        "salary_currency": employee.salary_currency,
        "base_salary": money_payload(employee.base_salary),
        "current_salary": money_payload(employee.current_salary),
        "current_bonus": money_payload(employee.current_bonus),
        "position": position_payload(employee.position) if employee.position_id else None,
        "reporting_manager": manager_payload(employee),
        "notes": employee.notes,
        "updated_at": employee.updated_at.isoformat(),
    }
    payload.update(leave_placeholder_payload())
    return payload


def employment_record_payload(record):
    return {
        "id": record.id,
        "status": record.status,
        "status_label": record.get_status_display(),
        "position": position_payload(record.position) if record.position_id else None,
        "start_date": record.start_date.isoformat() if record.start_date else None,
        "end_date": record.end_date.isoformat() if record.end_date else None,
        "notes": record.notes,
        "recorded_by": display_name(record.recorded_by) if record.recorded_by_id else "",
        "created_at": record.created_at.isoformat(),
    }


def salary_adjustment_payload(adjustment):
    return {
        "id": adjustment.id,
        "employee_id": adjustment.employee_id,
        "employee_name": display_name(adjustment.employee.profile),
        "employee_no": adjustment.employee.employee_no,
        "change_type": adjustment.change_type,
        "change_type_label": adjustment.get_change_type_display(),
        "amount": money_payload(adjustment.amount),
        "previous_salary": money_payload(adjustment.previous_salary),
        "new_salary": money_payload(adjustment.new_salary),
        "effective_date": adjustment.effective_date.isoformat() if adjustment.effective_date else None,
        "reason": adjustment.reason,
        "recorded_by": display_name(adjustment.recorded_by) if adjustment.recorded_by_id else "",
        "created_at": adjustment.created_at.isoformat(),
    }


def compensation_request_payload(request_obj):
    employee = request_obj.employee
    return {
        "id": request_obj.id,
        "employee": {
            "id": employee.id,
            "name": display_name(employee.profile),
            "employee_no": employee.employee_no,
            "role": employee.profile.role,
            "position": employee.position.title if employee.position_id else "",
            "currency": employee.salary_currency,
        },
        "request_type": request_obj.request_type,
        "request_type_label": request_obj.get_request_type_display(),
        "change_type": request_obj.change_type,
        "change_type_label": request_obj.get_change_type_display(),
        "amount": money_payload(request_obj.amount),
        "previous_amount": money_payload(request_obj.previous_amount),
        "requested_amount": money_payload(request_obj.requested_amount),
        "effective_date": request_obj.effective_date.isoformat() if request_obj.effective_date else None,
        "reason": request_obj.reason,
        "status": request_obj.status,
        "status_label": request_obj.get_status_display(),
        "requested_by": _profile_payload(request_obj.requested_by),
        "reviewed_by": _profile_payload(request_obj.reviewed_by),
        "reviewed_at": request_obj.reviewed_at.isoformat() if request_obj.reviewed_at else None,
        "review_note": request_obj.review_note,
        "created_at": request_obj.created_at.isoformat(),
        "updated_at": request_obj.updated_at.isoformat(),
    }


def document_payload(document):
    return {
        "id": document.id,
        "document_type": document.document_type,
        "document_type_label": document.get_document_type_display(),
        "title": document.title,
        "expires_on": document.expires_on.isoformat() if document.expires_on else None,
        "uploaded_by": display_name(document.uploaded_by) if document.uploaded_by_id else "",
        "uploaded_at": document.uploaded_at.isoformat(),
    }


def employee_detail_payload(employee):
    detail = employee_payload(employee)
    detail.update(
        {
            "employment_records": [
                employment_record_payload(record)
                for record in employee.employment_records.select_related("position", "recorded_by", "recorded_by__user")[:20]
            ],
            "salary_adjustments": [
                salary_adjustment_payload(adjustment)
                for adjustment in employee.salary_adjustments.select_related("employee__profile__user", "recorded_by", "recorded_by__user")[:20]
            ],
            "compensation_requests": [
                compensation_request_payload(item)
                for item in employee.compensation_requests.select_related(
                    "employee__profile__user",
                    "employee__position",
                    "requested_by",
                    "requested_by__user",
                    "reviewed_by",
                    "reviewed_by__user",
                )[:20]
            ],
            "documents": [document_payload(document) for document in employee.documents.select_related("uploaded_by", "uploaded_by__user")[:20]],
            "direct_reports": [
                {
                    "id": report.id,
                    "name": display_name(report.profile),
                    "employee_no": report.employee_no,
                    "position": report.position.title if report.position_id else "",
                }
                for report in employee.direct_reports.select_related("profile", "profile__user", "position")[:20]
            ],
        }
    )
    return detail


def hr_staff_payload(staff):
    profile = staff.profile
    return {
        "id": profile.id,
        "username": profile.user.username,
        "name": display_name(profile),
        "email": profile.user.email,
        "staff_id": profile.staff_id or staff.staff_id,
        "designation": profile.designation or staff.designation,
        "phone": profile.phone,
        "office_location": staff.office_location,
        "is_active": bool(profile.is_active and profile.user.is_active),
    }


def employee_profile_options():
    profiles = (
        Profile.objects.select_related("user")
        .filter(role__in=EMPLOYEE_ROLES, is_active=True)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    employee_profile_ids = set(
        Employee.objects.filter(profile__in=profiles).values_list("profile_id", flat=True)
    )
    return [
        {
            "id": profile.id,
            "name": display_name(profile),
            "email": profile.user.email,
            "role": profile.role,
            "identifier": profile_identifier(profile),
            "has_employee_record": profile.id in employee_profile_ids,
        }
        for profile in profiles[:250]
    ]


def _status_counts(employees):
    rows = employees.values("employment_status").annotate(count=Count("id"))
    counts = {row["employment_status"]: row["count"] for row in rows}
    return [
        {"status": status, "label": label, "count": counts.get(status, 0)}
        for status, label in Employee.STATUS_CHOICES
    ]


def _role_counts(employees, limit=None):
    rows = employees.values("profile__role").annotate(count=Count("id")).order_by("-count", "profile__role")
    if limit:
        rows = rows[:limit]
    return [
        {"role": row["profile__role"], "count": row["count"]}
        for row in rows
    ]


def _position_counts(employees, limit=None):
    rows = (
        employees.values("position__title", "position__code")
        .annotate(count=Count("id"))
        .order_by("-count", "position__title")
    )
    if limit:
        rows = rows[:limit]
    return [
        {
            "title": row["position__title"] or "Unassigned",
            "code": row["position__code"] or "",
            "count": row["count"],
        }
        for row in rows
    ]


def _money_bands(employees, field_name):
    bands = [
        ("0-1,999", Decimal("0.00"), Decimal("1999.99")),
        ("2,000-3,999", Decimal("2000.00"), Decimal("3999.99")),
        ("4,000-5,999", Decimal("4000.00"), Decimal("5999.99")),
        ("6,000-7,999", Decimal("6000.00"), Decimal("7999.99")),
        ("8,000+", Decimal("8000.00"), None),
    ]
    rows = []
    for label, low, high in bands:
        query = {f"{field_name}__gte": low}
        if high is not None:
            query[f"{field_name}__lte"] = high
        rows.append({"label": label, "count": employees.filter(**query).count()})
    return rows


def dashboard_payload():
    employees = Employee.objects.select_related("position", "profile", "profile__user")
    payroll = employees.aggregate(
        total_salary=Sum("current_salary"),
        average_salary=Avg("current_salary"),
        total_bonus=Sum("current_bonus"),
        average_bonus=Avg("current_bonus"),
    )
    today = timezone.localdate()
    expiring_documents = EmployeeDocument.objects.filter(
        expires_on__gte=today,
        expires_on__lte=today + timedelta(days=30),
    ).count()
    recent_records = EmploymentRecord.objects.select_related(
        "employee",
        "employee__profile",
        "employee__profile__user",
        "position",
        "recorded_by",
        "recorded_by__user",
    )[:8]
    recent_adjustments = SalaryAdjustment.objects.select_related(
        "employee",
        "employee__profile",
        "employee__profile__user",
        "recorded_by",
        "recorded_by__user",
    )[:8]
    recent_requests = CompensationChangeRequest.objects.select_related(
        "employee",
        "employee__profile",
        "employee__profile__user",
        "employee__position",
        "requested_by",
        "requested_by__user",
        "reviewed_by",
        "reviewed_by__user",
    )[:8]

    return {
        "summary": {
            "employees": employees.count(),
            "active": employees.filter(employment_status=Employee.STATUS_ACTIVE).count(),
            "probation": employees.filter(employment_status=Employee.STATUS_PROBATION).count(),
            "suspended": employees.filter(employment_status=Employee.STATUS_SUSPENDED).count(),
            "positions": Position.objects.filter(is_active=True).count(),
            "employees_without_position": employees.filter(position__isnull=True).count(),
            "documents_expiring_soon": expiring_documents,
            "monthly_payroll": money_payload(payroll["total_salary"]),
            "average_salary": money_payload(payroll["average_salary"]),
            "total_bonus": money_payload(payroll["total_bonus"]),
            "average_bonus": money_payload(payroll["average_bonus"]),
            "pending_compensation_requests": CompensationChangeRequest.objects.filter(status=CompensationChangeRequest.STATUS_PENDING).count(),
            "vacation_days_available": employees.count() * 21,
        },
        "statistics": {
            "status_counts": _status_counts(employees),
            "role_counts": _role_counts(employees),
            "position_counts": _position_counts(employees, limit=8),
            "recent_records": [employment_record_payload(record) for record in recent_records],
            "recent_salary_adjustments": [salary_adjustment_payload(adjustment) for adjustment in recent_adjustments],
            "recent_compensation_requests": [compensation_request_payload(item) for item in recent_requests],
        },
        "employees": [employee_payload(employee) for employee in employees[:25]],
        "positions": [position_payload(position) for position in Position.objects.filter(is_active=True)[:50]],
    }


def hr_statistics_payload():
    employees = Employee.objects.select_related("position", "profile", "profile__user")
    requests = CompensationChangeRequest.objects.all()
    payroll = employees.aggregate(
        total_salary=Sum("current_salary"),
        average_salary=Avg("current_salary"),
        total_bonus=Sum("current_bonus"),
        average_bonus=Avg("current_bonus"),
    )
    request_status_counts = {
        row["status"]: row["count"]
        for row in requests.values("status").annotate(count=Count("id"))
    }
    request_type_counts = {
        row["request_type"]: row["count"]
        for row in requests.values("request_type").annotate(count=Count("id"))
    }
    total_employees = employees.count()
    leave = leave_placeholder_payload()
    return {
        "summary": {
            "employees": total_employees,
            "active": employees.filter(employment_status=Employee.STATUS_ACTIVE).count(),
            "positions": Position.objects.filter(is_active=True).count(),
            "monthly_payroll": money_payload(payroll["total_salary"]),
            "average_salary": money_payload(payroll["average_salary"]),
            "total_bonus": money_payload(payroll["total_bonus"]),
            "average_bonus": money_payload(payroll["average_bonus"]),
            "pending_compensation_requests": request_status_counts.get(CompensationChangeRequest.STATUS_PENDING, 0),
            "vacation_days_total": total_employees * leave["vacation_days_total"],
            "vacation_days_used": total_employees * leave["vacation_days_used"],
            "vacation_days_remaining": total_employees * leave["vacation_days_remaining"],
            "leave_placeholder": True,
        },
        "charts": {
            "status_counts": _status_counts(employees),
            "role_counts": _role_counts(employees),
            "position_counts": _position_counts(employees, limit=10),
            "salary_bands": _money_bands(employees, "current_salary"),
            "bonus_bands": _money_bands(employees, "current_bonus"),
            "compensation_request_status": [
                {"status": status, "label": label, "count": request_status_counts.get(status, 0)}
                for status, label in CompensationChangeRequest.STATUS_CHOICES
            ],
            "compensation_request_types": [
                {"type": request_type, "label": label, "count": request_type_counts.get(request_type, 0)}
                for request_type, label in CompensationChangeRequest.REQUEST_CHOICES
            ],
            "leave_placeholder": [
                {"label": "Vacation Used", "count": total_employees * leave["vacation_days_used"]},
                {"label": "Vacation Remaining", "count": total_employees * leave["vacation_days_remaining"]},
                {"label": "Leave Used", "count": total_employees * leave["leave_days_used"]},
                {"label": "Leave Remaining", "count": total_employees * leave["leave_days_remaining"]},
            ],
        },
        "recent_compensation_requests": [
            compensation_request_payload(item)
            for item in requests.select_related(
                "employee",
                "employee__profile",
                "employee__profile__user",
                "employee__position",
                "requested_by",
                "requested_by__user",
                "reviewed_by",
                "reviewed_by__user",
            )[:20]
        ],
    }


@transaction.atomic
def create_or_update_position(*, data):
    code = str(data.get("code") or "").strip().upper()
    title = str(data.get("title") or "").strip()
    if not code:
        raise ValidationError({"code": "Position code is required."})
    if not title:
        raise ValidationError({"title": "Position title is required."})

    position_id = data.get("position_id") or data.get("id")
    position = Position.objects.filter(pk=position_id).first() if position_id else None
    if position is None:
        position = Position(code=code)
    elif Position.objects.exclude(pk=position.pk).filter(code=code).exists():
        raise ValidationError({"code": "Another position already uses this code."})

    position.code = code
    position.title = title
    position.employment_type = data.get("employment_type") or Position.EMPLOYMENT_FULL_TIME
    position.grade = str(data.get("grade") or "").strip()
    position.department_id = data.get("department_id") or None
    position.unit_id = data.get("unit_id") or None
    if "is_active" in data:
        position.is_active = bool(data.get("is_active"))
    position.save()
    return position


@transaction.atomic
def create_or_update_employee(*, actor, data):
    profile_id = data.get("profile_id")
    employee_id = data.get("employee_id") or data.get("id")
    employee = Employee.objects.select_for_update().filter(pk=employee_id).first() if employee_id else None
    is_new = employee is None

    if employee is None:
        profile = Profile.objects.select_related("user").filter(pk=profile_id, role__in=EMPLOYEE_ROLES).first()
        if profile is None:
            raise ValidationError({"profile_id": "Select an active university staff profile."})
        employee_no = str(data.get("employee_no") or profile_identifier(profile)).strip()
        if not employee_no:
            raise ValidationError({"employee_no": "Employee number is required."})
        employee = Employee(profile=profile, employee_no=employee_no, created_by=actor)
    else:
        profile = employee.profile
        if "employee_no" in data:
            employee.employee_no = str(data.get("employee_no") or "").strip()

    if Employee.objects.exclude(pk=employee.pk).filter(employee_no=employee.employee_no).exists():
        raise ValidationError({"employee_no": "Another employee already uses this number."})

    if "employment_status" in data:
        employee.employment_status = data.get("employment_status") or Employee.STATUS_ACTIVE
    if "position_id" in data:
        employee.position_id = data.get("position_id") or None
    if "reporting_manager_id" in data:
        employee.reporting_manager_id = data.get("reporting_manager_id") or None
    if "joining_date" in data and data.get("joining_date"):
        employee.joining_date = data.get("joining_date")
    if "work_email" in data:
        employee.work_email = str(data.get("work_email") or "").strip()
    if "salary_currency" in data:
        fallback_currency = default_currency_code()
        employee.salary_currency = str(data.get("salary_currency") or fallback_currency).strip().upper()[:3] or fallback_currency
    if "base_salary" in data:
        employee.base_salary = parse_money(data.get("base_salary"), "base_salary")
    if "current_salary" in data:
        employee.current_salary = parse_money(data.get("current_salary"), "current_salary")
    elif is_new and "base_salary" in data:
        employee.current_salary = employee.base_salary
    if "current_bonus" in data:
        employee.current_bonus = parse_money(data.get("current_bonus"), "current_bonus")
    if "notes" in data:
        employee.notes = str(data.get("notes") or "").strip()
    employee.updated_by = actor
    employee.save()

    EmploymentRecord.objects.create(
        employee=employee,
        status=employee.employment_status,
        position=employee.position,
        start_date=employee.joining_date or timezone.localdate(),
        recorded_by=actor,
        notes="Employee master updated.",
    )
    return employee


def _requested_amount(previous_amount, change_type, amount):
    if change_type == CompensationChangeRequest.TYPE_INCREASE:
        return previous_amount + amount
    if change_type == CompensationChangeRequest.TYPE_DECREASE:
        if amount > previous_amount:
            raise ValidationError({"amount": "Decrease cannot be greater than the current amount."})
        return previous_amount - amount
    return amount


@transaction.atomic
def create_compensation_request(*, actor, employee_id, data):
    employee = Employee.objects.select_for_update().filter(pk=employee_id).first()
    if employee is None:
        raise ValidationError({"employee_id": "Employee record was not found."})

    request_type = data.get("request_type") or CompensationChangeRequest.REQUEST_SALARY
    if request_type not in dict(CompensationChangeRequest.REQUEST_CHOICES):
        raise ValidationError({"request_type": "Select salary or bonus."})

    change_type = data.get("change_type")
    if change_type not in dict(CompensationChangeRequest.TYPE_CHOICES):
        raise ValidationError({"change_type": "Select increase, decrease, or set amount."})

    amount = parse_money(data.get("amount"), "amount", allow_zero=False)
    previous_amount = employee.current_salary if request_type == CompensationChangeRequest.REQUEST_SALARY else employee.current_bonus
    requested_amount = _requested_amount(previous_amount or Decimal("0.00"), change_type, amount)
    if requested_amount == (previous_amount or Decimal("0.00")):
        raise ValidationError({"amount": "Requested amount must change the current amount."})

    request_obj = CompensationChangeRequest(
        employee=employee,
        request_type=request_type,
        change_type=change_type,
        amount=amount,
        previous_amount=previous_amount or Decimal("0.00"),
        requested_amount=requested_amount,
        effective_date=data.get("effective_date") or timezone.localdate(),
        reason=str(data.get("reason") or "").strip(),
        requested_by=actor,
    )
    request_obj.save()
    return request_obj


def create_salary_adjustment(*, actor, employee_id, data):
    payload = dict(data)
    payload["request_type"] = CompensationChangeRequest.REQUEST_SALARY
    return create_compensation_request(actor=actor, employee_id=employee_id, data=payload)


def compensation_requests_payload(*, status_value=None):
    requests = CompensationChangeRequest.objects.select_related(
        "employee",
        "employee__profile",
        "employee__profile__user",
        "employee__position",
        "requested_by",
        "requested_by__user",
        "reviewed_by",
        "reviewed_by__user",
    )
    if status_value:
        requests = requests.filter(status=status_value)
    return {
        "requests": [compensation_request_payload(item) for item in requests[:200]],
        "summary": {
            "pending": CompensationChangeRequest.objects.filter(status=CompensationChangeRequest.STATUS_PENDING).count(),
            "approved": CompensationChangeRequest.objects.filter(status=CompensationChangeRequest.STATUS_APPROVED).count(),
            "rejected": CompensationChangeRequest.objects.filter(status=CompensationChangeRequest.STATUS_REJECTED).count(),
        },
    }


@transaction.atomic
def review_compensation_request(*, actor, request_id, status_value, review_note=""):
    request_obj = CompensationChangeRequest.objects.select_for_update().filter(pk=request_id).first()
    if request_obj is None:
        raise ValidationError({"request_id": "Compensation request was not found."})
    employee = (
        Employee.objects.select_for_update()
        .select_related("profile", "profile__user")
        .get(pk=request_obj.employee_id)
    )
    request_obj.employee = employee
    if request_obj.status != CompensationChangeRequest.STATUS_PENDING:
        raise ValidationError({"status": "Only pending compensation requests can be reviewed."})
    if status_value not in {CompensationChangeRequest.STATUS_APPROVED, CompensationChangeRequest.STATUS_REJECTED}:
        raise ValidationError({"status": "Select approved or rejected."})

    request_obj.status = status_value
    request_obj.reviewed_by = actor
    request_obj.reviewed_at = timezone.now()
    request_obj.review_note = str(review_note or "").strip()
    request_obj.save()

    if status_value == CompensationChangeRequest.STATUS_APPROVED:
        if request_obj.request_type == CompensationChangeRequest.REQUEST_SALARY:
            adjustment_change_type = (
                SalaryAdjustment.TYPE_DECREASE
                if request_obj.requested_amount < request_obj.previous_amount
                else SalaryAdjustment.TYPE_INCREASE
            )
            adjustment = SalaryAdjustment(
                employee=employee,
                change_type=adjustment_change_type,
                amount=abs(request_obj.requested_amount - request_obj.previous_amount),
                previous_salary=request_obj.previous_amount,
                new_salary=request_obj.requested_amount,
                effective_date=request_obj.effective_date,
                reason=request_obj.reason,
                recorded_by=actor,
            )
            adjustment.save()
            employee.current_salary = request_obj.requested_amount
            employee.updated_by = actor
            employee.save(update_fields=["current_salary", "updated_by", "updated_at"])
        else:
            employee.current_bonus = request_obj.requested_amount
            employee.updated_by = actor
            employee.save(update_fields=["current_bonus", "updated_by", "updated_at"])

    return request_obj
