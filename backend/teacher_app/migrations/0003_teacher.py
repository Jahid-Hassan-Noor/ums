# Generated manually to add the teacher role detail table.

import django.db.models.deletion
from django.db import migrations, models


def backfill_teachers(apps, schema_editor):
    Profile = apps.get_model("admin_app", "Profile")
    Teacher = apps.get_model("teacher_app", "Teacher")

    for profile in Profile.objects.filter(role="teacher"):
        Teacher.objects.get_or_create(
            profile=profile,
            defaults={
                "staff_id": profile.staff_id,
                "designation": profile.designation,
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0004_adminprofile_profile_defaults"),
        ("teacher_app", "0002_assignment_allow_late_submissions_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Teacher",
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
                ("staff_id", models.CharField(blank=True, max_length=50)),
                ("designation", models.CharField(blank=True, max_length=255)),
                ("academic_rank", models.CharField(blank=True, max_length=100)),
                ("specialization", models.CharField(blank=True, max_length=255)),
                ("office_location", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teacher_detail",
                        to="admin_app.profile",
                    ),
                ),
            ],
        ),
        migrations.RunPython(backfill_teachers, noop_reverse),
    ]
