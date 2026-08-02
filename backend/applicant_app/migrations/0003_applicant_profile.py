# Generated manually to attach applicants to Profile instead of User.

import django.db.models.deletion
from django.db import migrations, models


def migrate_applicant_profiles(apps, schema_editor):
    Applicant = apps.get_model("applicant_app", "Applicant")
    Profile = apps.get_model("admin_app", "Profile")

    for applicant in Applicant.objects.select_related("user").all():
        profile, _created = Profile.objects.get_or_create(
            user=applicant.user,
            defaults={
                "role": "applicant",
                "phone": applicant.phone,
            },
        )
        update_fields = []
        if profile.role != "applicant":
            profile.role = "applicant"
            update_fields.append("role")
        if applicant.phone and not profile.phone:
            profile.phone = applicant.phone
            update_fields.append("phone")
        if update_fields:
            profile.save(update_fields=update_fields + ["updated_at"])

        applicant.profile = profile
        applicant.save(update_fields=["profile"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0004_adminprofile_profile_defaults"),
        ("applicant_app", "0002_seed_application_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicant",
            name="profile",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applicant_detail",
                to="admin_app.profile",
            ),
        ),
        migrations.RunPython(migrate_applicant_profiles, noop_reverse),
        migrations.AlterField(
            model_name="applicant",
            name="profile",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applicant_detail",
                to="admin_app.profile",
            ),
        ),
        migrations.RemoveField(
            model_name="applicant",
            name="user",
        ),
    ]
