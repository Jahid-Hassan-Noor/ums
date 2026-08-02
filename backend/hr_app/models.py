from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class HRStaff(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="hr_detail",
    )
    hr_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    office_location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.hr_id

    @staff_id.setter
    def staff_id(self, value):
        self.hr_id = value


class Position(models.Model):
    EMPLOYMENT_FULL_TIME = "full_time"
    EMPLOYMENT_PART_TIME = "part_time"
    EMPLOYMENT_CONTRACT = "contract"
    EMPLOYMENT_ADJUNCT = "adjunct"
    EMPLOYMENT_CHOICES = [
        (EMPLOYMENT_FULL_TIME, "Full-time"),
        (EMPLOYMENT_PART_TIME, "Part-time"),
        (EMPLOYMENT_CONTRACT, "Contract"),
        (EMPLOYMENT_ADJUNCT, "Adjunct"),
    ]

    code = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=160)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default=EMPLOYMENT_FULL_TIME)
    grade = models.CharField(max_length=40, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title", "code")

    def __str__(self):
        return f"{self.title} ({self.code})"

    def clean(self):
        if self.unit_id and self.department_id and self.unit.department_id != self.department_id:
            raise ValidationError({"unit": "Selected unit must belong to the selected department."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Employee(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_PROBATION = "probation"
    STATUS_SUSPENDED = "suspended"
    STATUS_RESIGNED = "resigned"
    STATUS_TERMINATED = "terminated"
    STATUS_RETIRED = "retired"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_PROBATION, "Probation"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_RESIGNED, "Resigned"),
        (STATUS_TERMINATED, "Terminated"),
        (STATUS_RETIRED, "Retired"),
    ]

    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="employee_record",
    )
    employee_no = models.CharField(max_length=50, unique=True)
    employment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    reporting_manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="direct_reports")
    joining_date = models.DateField(default=timezone.localdate)
    work_email = models.EmailField(blank=True)
    salary_currency = models.CharField(max_length=3, default="MYR")
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    current_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_employee_records",
    )
    updated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_employee_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("profile__user__first_name", "profile__user__last_name", "employee_no")
        indexes = [
            models.Index(fields=("employment_status",)),
            models.Index(fields=("employee_no",)),
        ]

    def __str__(self):
        return self.employee_no

    def clean(self):
        if self.reporting_manager_id and self.reporting_manager_id == self.pk:
            raise ValidationError({"reporting_manager": "Employee cannot report to themselves."})
        if self.base_salary < 0:
            raise ValidationError({"base_salary": "Base salary cannot be negative."})
        if self.current_salary < 0:
            raise ValidationError({"current_salary": "Current salary cannot be negative."})
        if self.current_bonus < 0:
            raise ValidationError({"current_bonus": "Current bonus cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class EmploymentRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employment_records")
    status = models.CharField(max_length=20, choices=Employee.STATUS_CHOICES, default=Employee.STATUS_ACTIVE)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_employment_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_date", "-created_at")


class SalaryAdjustment(models.Model):
    TYPE_INCREASE = "increase"
    TYPE_DECREASE = "decrease"
    TYPE_CHOICES = [
        (TYPE_INCREASE, "Increase"),
        (TYPE_DECREASE, "Decrease"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="salary_adjustments")
    change_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    previous_salary = models.DecimalField(max_digits=12, decimal_places=2)
    new_salary = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField(default=timezone.localdate)
    reason = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_salary_adjustments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-effective_date", "-created_at")
        indexes = [
            models.Index(fields=("employee", "effective_date"), name="hr_sal_emp_eff_idx"),
            models.Index(fields=("change_type",), name="hr_sal_type_idx"),
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Adjustment amount must be greater than zero."})
        if self.previous_salary < 0 or self.new_salary < 0:
            raise ValidationError("Salary values cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CompensationChangeRequest(models.Model):
    REQUEST_SALARY = "salary"
    REQUEST_BONUS = "bonus"
    REQUEST_CHOICES = [
        (REQUEST_SALARY, "Salary"),
        (REQUEST_BONUS, "Bonus"),
    ]

    TYPE_INCREASE = "increase"
    TYPE_DECREASE = "decrease"
    TYPE_SET = "set"
    TYPE_CHOICES = [
        (TYPE_INCREASE, "Increase"),
        (TYPE_DECREASE, "Decrease"),
        (TYPE_SET, "Set amount"),
    ]

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="compensation_requests")
    request_type = models.CharField(max_length=20, choices=REQUEST_CHOICES)
    change_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    previous_amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField(default=timezone.localdate)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_compensation_changes",
    )
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_compensation_changes",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "request_type"), name="hr_comp_status_type_idx"),
            models.Index(fields=("employee", "status"), name="hr_comp_emp_status_idx"),
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Change amount must be greater than zero."})
        if self.previous_amount < 0 or self.requested_amount < 0:
            raise ValidationError("Compensation amounts cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class EmployeeDocument(models.Model):
    DOCUMENT_CONTRACT = "contract"
    DOCUMENT_ID = "identity"
    DOCUMENT_CERTIFICATE = "certificate"
    DOCUMENT_OTHER = "other"
    DOCUMENT_CHOICES = [
        (DOCUMENT_CONTRACT, "Contract"),
        (DOCUMENT_ID, "Identity document"),
        (DOCUMENT_CERTIFICATE, "Certificate"),
        (DOCUMENT_OTHER, "Other"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DOCUMENT_CHOICES, default=DOCUMENT_OTHER)
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="hr/employee-documents/", null=True, blank=True)
    expires_on = models.DateField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_employee_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)
