import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("admin_app", "0032_add_hr_role"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Profile",
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
                        (
                            "role",
                            models.CharField(
                                choices=[
                                    ("student", "Student"),
                                    ("teacher", "Teacher"),
                                    ("executive", "Executive"),
                                    ("librarian", "Librarian"),
                                    ("caterer", "Caterer"),
                                    ("technician", "Technician"),
                                    ("accountant", "Accountant"),
                                    ("hr", "Human Resources"),
                                    ("admin", "Admin"),
                                    ("applicant", "Applicant"),
                                ],
                                default="student",
                                max_length=20,
                            ),
                        ),
                        ("date_of_birth", models.DateField(blank=True, null=True)),
                        ("phone", models.CharField(blank=True, max_length=30)),
                        (
                            "profile_picture",
                            models.ImageField(
                                blank=True,
                                null=True,
                                upload_to="profiles/pictures/",
                            ),
                        ),
                        (
                            "password_reset_token",
                            models.CharField(blank=True, max_length=255, null=True),
                        ),
                        ("password_reset_requested_at", models.DateTimeField(blank=True, null=True)),
                        ("is_active", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "user",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="profile",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "admin_app_profile",
                    },
                ),
                migrations.CreateModel(
                    name="Admin",
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
                        ("admin_id", models.CharField(blank=True, db_index=True, max_length=50)),
                        ("designation", models.CharField(blank=True, max_length=255)),
                        ("access_notes", models.TextField(blank=True)),
                        ("is_active", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "center",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="admin_app.center",
                            ),
                        ),
                        (
                            "department",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="admin_app.department",
                            ),
                        ),
                        (
                            "profile",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="admin_detail",
                                to="auth_app.profile",
                            ),
                        ),
                        (
                            "school",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="admin_app.school",
                            ),
                        ),
                        (
                            "unit",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="admin_app.unit",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "admin_app_admin",
                        "verbose_name": "Admin",
                        "verbose_name_plural": "Admins",
                    },
                ),
            ],
        ),
    ]
