from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class Caterer(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="caterer_detail",
    )
    caterer_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    canteen_location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.caterer_id

    @staff_id.setter
    def staff_id(self, value):
        self.caterer_id = value


class CanteenSetting(models.Model):
    monthly_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("50.00"),
    )
    updated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_canteen_settings",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.monthly_allowance < 0:
            raise ValidationError({"monthly_allowance": "Monthly allowance cannot be negative."})

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)


class CanteenMonthlyBonus(models.Model):
    month = models.DateField(unique=True)
    extra_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    occasion = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_canteen_bonuses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-month",)

    def clean(self):
        if self.month and self.month.day != 1:
            raise ValidationError({"month": "Bonus month must be the first day of a month."})
        if self.extra_amount < 0:
            raise ValidationError({"extra_amount": "Extra amount cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StudentCanteenAccount(models.Model):
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="canteen_accounts",
    )
    month = models.DateField()
    allowance_amount = models.DecimalField(max_digits=8, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-month", "student__user__username")
        constraints = [
            models.UniqueConstraint(
                fields=("student", "month"),
                name="unique_student_canteen_account_month",
            )
        ]

    @property
    def adjustment_amount(self):
        return self.adjustments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    @property
    def balance(self):
        return self.allowance_amount + self.adjustment_amount - self.spent_amount

    def clean(self):
        if self.student_id and self.student.role != "student":
            raise ValidationError({"student": "Canteen accounts can only belong to students."})
        if self.allowance_amount < 0 or self.spent_amount < 0:
            raise ValidationError("Allowance and spent amounts cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CanteenTransaction(models.Model):
    account = models.ForeignKey(
        StudentCanteenAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    caterer = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.PROTECT,
        related_name="canteen_transactions",
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Transaction amount must be greater than zero."})
        if self.caterer_id and self.caterer.role != "caterer":
            raise ValidationError({"caterer": "Transactions must be recorded by a Caterer account."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CanteenBalanceAdjustment(models.Model):
    account = models.ForeignKey(
        StudentCanteenAccount,
        on_delete=models.PROTECT,
        related_name="adjustments",
    )
    added_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.PROTECT,
        related_name="canteen_balance_adjustments",
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Added balance must be greater than zero."})
        if not self.reason.strip():
            raise ValidationError({"reason": "A reason is required for manual balance additions."})
        if self.added_by_id and self.added_by.role != "accountant":
            raise ValidationError({"added_by": "Only accountants can add student canteen balance."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
