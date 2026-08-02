# Generated manually to add role detail lifecycle tables.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_profiles_and_admin_details(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    Profile = apps.get_model("admin_app", "Profile")
    AdminProfile = apps.get_model("admin_app", "AdminProfile")

    for user in User.objects.all():
        role = "admin" if user.is_superuser else "student"
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={"role": role},
        )
        if user.is_superuser and not created and profile.role != "admin":
            profile.role = "admin"
            profile.save(update_fields=["role", "updated_at"])

    for profile in Profile.objects.filter(role="admin"):
        AdminProfile.objects.get_or_create(
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
        ("admin_app", "0003_alter_profile_role"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="profile",
            name="role",
            field=models.CharField(
                choices=[
                    ("student", "Student"),
                    ("teacher", "Teacher"),
                    ("executive", "Executive"),
                    ("admin", "Admin"),
                    ("applicant", "Applicant"),
                ],
                default="student",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="AdminProfile",
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
                ("access_notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="admin_detail",
                        to="admin_app.profile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Admin",
                "verbose_name_plural": "Admins",
            },
        ),
        migrations.RunPython(backfill_profiles_and_admin_details, noop_reverse),
    ]
