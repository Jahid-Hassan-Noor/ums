import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0007_course_scope_classmeeting_adjustments"),
    ]

    operations = [
        migrations.CreateModel(
            name="Hostel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=30, unique=True)),
                ("name", models.CharField(blank=True, max_length=255)),
                (
                    "hostel_type",
                    models.CharField(choices=[("male", "Male"), ("female", "Female")], max_length=10),
                ),
                ("warden_name", models.CharField(blank=True, max_length=255)),
                ("warden_phone", models.CharField(blank=True, max_length=30)),
                ("warden_email", models.EmailField(blank=True, max_length=254)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "warden",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hostels_wardened",
                        to="admin_app.profile",
                    ),
                ),
            ],
            options={
                "ordering": ("code",),
            },
        ),
        migrations.CreateModel(
            name="HostelRoom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("floor", models.PositiveSmallIntegerField()),
                ("number", models.CharField(max_length=20)),
                ("code", models.CharField(blank=True, max_length=80, unique=True)),
                ("capacity", models.PositiveSmallIntegerField(default=4)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "hostel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rooms",
                        to="admin_app.hostel",
                    ),
                ),
            ],
            options={
                "ordering": ("hostel__code", "floor", "number"),
                "unique_together": {("hostel", "floor", "number")},
            },
        ),
    ]
