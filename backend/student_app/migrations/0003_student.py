# Generated manually to add the student role detail table.

import django.db.models.deletion
from django.db import migrations, models


def backfill_students(apps, schema_editor):
    Profile = apps.get_model("admin_app", "Profile")
    Student = apps.get_model("student_app", "Student")

    for profile in Profile.objects.filter(role="student"):
        Student.objects.get_or_create(
            profile=profile,
            defaults={"student_id": profile.student_id},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0004_adminprofile_profile_defaults"),
        ("student_app", "0002_emergencycontact_studentaffairscontact_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("student_id", models.CharField(blank=True, max_length=50)),
                ("admission_number", models.CharField(blank=True, max_length=50)),
                ("enrollment_status", models.CharField(blank=True, max_length=50)),
                ("current_year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("expected_graduation_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_detail",
                        to="admin_app.profile",
                    ),
                ),
            ],
        ),
        migrations.RunPython(backfill_students, noop_reverse),
    ]
