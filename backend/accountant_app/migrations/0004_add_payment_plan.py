from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("admin_app", "0001_initial"),
        ("accountant_app", "0003_add_student_charge_and_ledger"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(blank=True, max_length=500)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="MYR", max_length=3)),
                ("installment_count", models.PositiveSmallIntegerField(default=2)),
                ("frequency", models.CharField(choices=[("monthly", "Monthly"), ("weekly", "Weekly"), ("biweekly", "Biweekly")], default="monthly", max_length=20)),
                ("status", models.CharField(choices=[("active", "Active"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_payment_plans", to="admin_app.profile")),
                ("charge", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payment_plans", to="accountant_app.studentcharge")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_payment_plans", to="admin_app.profile")),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="PaymentPlanInstallment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("installment_number", models.PositiveSmallIntegerField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("due_date", models.DateField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("overdue", "Overdue"), ("cancelled", "Cancelled")], default="pending", max_length=20)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="installments", to="accountant_app.paymentplan")),
                ("ledger_entry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="plan_installments", to="accountant_app.studentledgerentry")),
            ],
            options={
                "ordering": ("plan", "installment_number"),
            },
        ),
        migrations.AddIndex(
            model_name="paymentplan",
            index=models.Index(fields=["student", "status"], name="accountant__student_status_idx"),
        ),
        migrations.AddIndex(
            model_name="paymentplaninstallment",
            index=models.Index(fields=["plan", "status"], name="accountant__plan_status_idx"),
        ),
        migrations.AddIndex(
            model_name="paymentplaninstallment",
            index=models.Index(fields=["due_date", "status"], name="accountant__due_date_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="paymentplaninstallment",
            constraint=models.UniqueConstraint(fields=("plan", "installment_number"), name="unique_installment_number_per_plan"),
        ),
    ]
