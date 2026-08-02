from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin_app", "0027_remove_admin_timetable_import"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="password_reset_requested_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
