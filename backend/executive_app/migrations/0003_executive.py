# Generated manually to add the executive role detail table.

import django.db.models.deletion
from django.db import migrations, models


def backfill_executives(apps, schema_editor):
    Profile = apps.get_model("admin_app", "Profile")
    Executive = apps.get_model("executive_app", "Executive")

    for profile in Profile.objects.filter(role="executive"):
        Executive.objects.get_or_create(
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
        ("executive_app", "0002_election_published_by_election_results_published_at_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Executive",
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
                ("office_location", models.CharField(blank=True, max_length=255)),
                ("responsibility_area", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="executive_detail",
                        to="admin_app.profile",
                    ),
                ),
            ],
        ),
        migrations.RunPython(backfill_executives, noop_reverse),
    ]
