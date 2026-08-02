from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def subscription_role_values():
    from admin_app.models import Profile

    return [role for role, _label in Profile.ROLE_CHOICES if role != Profile.ROLE_APPLICANT]


def normalized_subscription_roles(value):
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValidationError({"available_roles": "Subscription roles must be a list."})

    valid_roles = subscription_role_values()
    incoming = {str(role).strip().lower() for role in value if str(role).strip()}
    unknown = sorted(incoming - set(valid_roles))
    if unknown:
        raise ValidationError({"available_roles": f"Unknown subscription roles: {', '.join(unknown)}."})
    return [role for role in valid_roles if role in incoming]


class Accountant(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="accountant_detail",
    )
    accountant_id = models.CharField(max_length=50, blank=True, db_index=True)
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
        return self.accountant_id

    @staff_id.setter
    def staff_id(self, value):
        self.accountant_id = value


class FinanceGatewayConfig(models.Model):
    PROVIDER_TOYYIBPAY = "toyyibpay"
    PROVIDER_CUSTOM = "custom"
    PROVIDER_CHOICES = [
        (PROVIDER_TOYYIBPAY, "ToyyibPay / DuitNow-compatible bill API"),
        (PROVIDER_CUSTOM, "Custom DuitNow merchant endpoint"),
    ]

    MODE_SANDBOX = "sandbox"
    MODE_PRODUCTION = "production"
    MODE_CHOICES = [
        (MODE_SANDBOX, "Sandbox"),
        (MODE_PRODUCTION, "Production"),
    ]

    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default=PROVIDER_TOYYIBPAY)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_SANDBOX)
    merchant_name = models.CharField(max_length=255, blank=True)
    api_base_url = models.URLField(max_length=500, blank=True)
    checkout_base_url = models.URLField(max_length=500, blank=True)
    category_code = models.CharField(max_length=120, blank=True)
    secret_key = models.CharField(max_length=500, blank=True)
    callback_token = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=False)
    updated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_finance_gateway_configs",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.is_active:
            required = {
                "api_base_url": self.api_base_url,
                "checkout_base_url": self.checkout_base_url,
                "category_code": self.category_code,
                "secret_key": self.secret_key,
            }
            missing = [field for field, value in required.items() if not str(value or "").strip()]
            if missing:
                raise ValidationError({field: "Required before enabling the gateway." for field in missing})

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def secret_key_preview(self):
        if not self.secret_key:
            return ""
        return f"••••{self.secret_key[-4:]}"

    @property
    def callback_token_preview(self):
        if not self.callback_token:
            return ""
        return f"••••{self.callback_token[-4:]}"


class SubscriptionPlan(models.Model):
    KIND_GYM = "gym"
    KIND_KITCHEN = "kitchen"

    subscription_type = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    duration_days = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    available_to_all_roles = models.BooleanField(default=True)
    available_roles = models.JSONField(default=list, blank=True)
    updated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_subscription_plans",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("subscription_type",)

    def clean(self):
        self.subscription_type = str(self.subscription_type or "").strip().lower()
        if not self.subscription_type:
            raise ValidationError({"subscription_type": "Subscription code is required."})
        if self.price < 0:
            raise ValidationError({"price": "Subscription price cannot be negative."})
        if self.duration_days < 1:
            raise ValidationError({"duration_days": "Subscription duration must be at least 1 day."})
        self.available_roles = normalized_subscription_roles(self.available_roles)
        if self.available_to_all_roles:
            self.available_roles = []
        elif not self.available_roles:
            raise ValidationError({"available_roles": "Choose at least one role or enable all roles."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending payment"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_FAILED, "Payment failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    subscriber = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="finance_subscriptions",
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="MYR")
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    external_reference = models.CharField(max_length=80, blank=True, null=True, unique=True)
    gateway_bill_code = models.CharField(max_length=120, blank=True, db_index=True)
    checkout_url = models.URLField(max_length=700, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    activated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activated_finance_subscriptions",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("subscriber", "status")),
            models.Index(fields=("plan", "status")),
        ]

    @property
    def is_current(self):
        return self.status == self.STATUS_ACTIVE and bool(self.ends_at and self.ends_at >= timezone.now())


class PaymentAttempt(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="payment_attempts")
    fine = models.ForeignKey(
        "Fine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_attempts",
    )
    payer = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="finance_payment_attempts",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="MYR")
    external_reference = models.CharField(max_length=80, unique=True)
    gateway_reference = models.CharField(max_length=120, blank=True, db_index=True)
    checkout_url = models.URLField(max_length=700, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    callback_payload = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("payer", "status")),
            models.Index(fields=("gateway_reference",)),
        ]

    def __str__(self):
        return self.external_reference


class Fine(models.Model):
    """An arbitrary fine or charge issued by an accountant to a student."""

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_OVERDUE = "overdue"
    STATUS_DEDUCTED = "deducted"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending payment")),
        (STATUS_PAID, _("Paid online")),
        (STATUS_OVERDUE, _("Overdue – awaiting manual deduction")),
        (STATUS_DEDUCTED, _("Deducted from meal allowance")),
    ]

    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_fines",
    )
    issued_by = models.ForeignKey(
        "Accountant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_fines",
    )
    reason = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="MYR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    due_date = models.DateTimeField(null=True, blank=True, help_text="Deadline for student to pay online. Leave blank for no deadline.")
    checkout_url = models.URLField(max_length=700, blank=True)
    gateway_bill_code = models.CharField(max_length=120, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    deducted_at = models.DateTimeField(null=True, blank=True)
    deducted_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_fine_deductions",
    )
    deduction_note = models.TextField(blank=True, help_text="Accountant note when manually deducting from meal allowance.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("student", "status")),
            models.Index(fields=("due_date",)),
        ]

    def __str__(self):
        return f"Fine #{self.pk} – {self.reason} – {self.amount} {self.currency}"

    def clean(self):
        if self.amount is not None and self.amount <= Decimal("0"):
            raise ValidationError({"amount": "Fine amount must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class FeeCategory(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "code")

    def __str__(self):
        return self.name

    def clean(self):
        self.code = str(self.code or "").strip().upper()
        if not self.code:
            raise ValidationError({"code": "Fee category code is required."})
        if not str(self.name or "").strip():
            raise ValidationError({"name": "Fee category name is required."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StudentCharge(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_POSTED = "posted"
    STATUS_WAIVED = "waived"
    STATUS_REVERSED = "reversed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_POSTED, "Posted"),
        (STATUS_WAIVED, "Waived"),
        (STATUS_REVERSED, "Reversed"),
    ]

    SOURCE_MANUAL = "manual"
    SOURCE_TUITION = "tuition"
    SOURCE_HOSTEL = "hostel"
    SOURCE_LIBRARY = "library"
    SOURCE_CANTEEN = "canteen"
    SOURCE_FINE = "fine"
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual"),
        (SOURCE_TUITION, "Tuition"),
        (SOURCE_HOSTEL, "Hostel"),
        (SOURCE_LIBRARY, "Library"),
        (SOURCE_CANTEEN, "Canteen"),
        (SOURCE_FINE, "Fine"),
    ]

    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_finance_charges",
    )
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="student_charges")
    source_type = models.CharField(max_length=30, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="MYR")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED)
    issued_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_student_charges",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("student", "status")),
            models.Index(fields=("source_type", "source_id")),
            models.Index(fields=("due_date",)),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("source_type", "source_id"),
                condition=models.Q(source_id__isnull=False),
                name="unique_student_charge_source",
            )
        ]

    def __str__(self):
        return f"{self.student_id} {self.description} {self.amount}"

    def clean(self):
        if self.amount is not None and self.amount <= Decimal("0"):
            raise ValidationError({"amount": "Charge amount must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StudentLedgerEntry(models.Model):
    ENTRY_DEBIT = "debit"
    ENTRY_PAYMENT = "payment"
    ENTRY_WAIVER = "waiver"
    ENTRY_REFUND = "refund"
    ENTRY_REVERSAL = "reversal"
    ENTRY_ADJUSTMENT = "adjustment"
    ENTRY_CHOICES = [
        (ENTRY_DEBIT, "Debit"),
        (ENTRY_PAYMENT, "Payment"),
        (ENTRY_WAIVER, "Waiver"),
        (ENTRY_REFUND, "Refund"),
        (ENTRY_REVERSAL, "Reversal"),
        (ENTRY_ADJUSTMENT, "Adjustment"),
    ]

    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_finance_ledger_entries",
    )
    charge = models.ForeignKey(StudentCharge, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    entry_type = models.CharField(max_length=20, choices=ENTRY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="MYR")
    description = models.CharField(max_length=500)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    posted_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_student_ledger_entries",
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("posted_at", "id")
        indexes = [
            models.Index(fields=("student", "posted_at")),
            models.Index(fields=("entry_type",)),
        ]

    def clean(self):
        if self.amount is not None and self.amount <= Decimal("0"):
            raise ValidationError({"amount": "Ledger amount must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StudentBalanceSnapshot(models.Model):
    student = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_finance_balance",
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="MYR")
    as_of = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("student__user__username",)


class StudentFinanceHold(models.Model):
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_finance_holds",
    )
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    placed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placed_student_finance_holds",
    )
    released_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="released_student_finance_holds",
    )
    placed_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-placed_at",)
        indexes = [
            models.Index(fields=("student", "is_active")),
        ]


class PaymentPlan(models.Model):
    FREQUENCY_MONTHLY = "monthly"
    FREQUENCY_WEEKLY = "weekly"
    FREQUENCY_BIWEEKLY = "biweekly"
    FREQUENCY_CHOICES = [
        (FREQUENCY_MONTHLY, "Monthly"),
        (FREQUENCY_WEEKLY, "Weekly"),
        (FREQUENCY_BIWEEKLY, "Biweekly"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_payment_plans",
    )
    charge = models.ForeignKey(
        StudentCharge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_plans",
    )
    description = models.CharField(max_length=500, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="MYR")
    installment_count = models.PositiveSmallIntegerField(default=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default=FREQUENCY_MONTHLY)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_payment_plans",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("student", "status")),
        ]

    def __str__(self):
        return f"Plan #{self.pk} – {self.student_id} – {self.total_amount} {self.currency}"

    def clean(self):
        if self.total_amount is not None and self.total_amount <= Decimal("0"):
            raise ValidationError({"total_amount": "Total amount must be greater than zero."})
        if self.installment_count < 2:
            raise ValidationError({"installment_count": "Installment count must be at least 2."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PaymentPlanInstallment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_OVERDUE = "overdue"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_OVERDUE, "Overdue"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    ledger_entry = models.ForeignKey(
        StudentLedgerEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plan_installments",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("plan", "installment_number")
        indexes = [
            models.Index(fields=("plan", "status")),
            models.Index(fields=("due_date", "status")),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("plan", "installment_number"),
                name="unique_installment_number_per_plan",
            )
        ]

    def __str__(self):
        return f"Plan #{self.plan_id} – Installment {self.installment_number} – {self.amount}"

    def clean(self):
        if self.amount is not None and self.amount <= Decimal("0"):
            raise ValidationError({"amount": "Installment amount must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
