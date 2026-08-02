import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("admin_app", "0032_add_hr_role"),
        ("auth_app", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Notification",
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
                        ("verb", models.CharField(max_length=255)),
                        ("unread", models.BooleanField(default=True)),
                        ("data", models.JSONField(blank=True, null=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "actor",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="acted_notifications",
                                to="auth_app.profile",
                            ),
                        ),
                        (
                            "recipient",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="notifications",
                                to="auth_app.profile",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "admin_app_notification",
                    },
                ),
            ],
        ),
    ]
