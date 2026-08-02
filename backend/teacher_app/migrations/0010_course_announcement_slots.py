import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teacher_app", "0009_assignment_upload_rules_and_activity_kind"),
    ]

    operations = [
        migrations.AlterField(
            model_name="courseannouncement",
            name="announcement_type",
            field=models.CharField(
                choices=[
                    ("general", "General"),
                    ("test", "Test"),
                    ("quiz", "Quiz"),
                    ("presentation", "Presentation"),
                ],
                default="general",
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="CourseAnnouncementSlot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(blank=True, max_length=255)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("capacity", models.PositiveSmallIntegerField(default=1)),
                (
                    "selection_type",
                    models.CharField(
                        choices=[("individual", "Individual"), ("group", "Group")],
                        default="individual",
                        max_length=20,
                    ),
                ),
                ("instructions", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "announcement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slots",
                        to="teacher_app.courseannouncement",
                    ),
                ),
            ],
            options={"ordering": ("starts_at", "id")},
        ),
        migrations.CreateModel(
            name="CourseAnnouncementSlotSelection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("group_name", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "announcement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slot_selections",
                        to="teacher_app.courseannouncement",
                    ),
                ),
                (
                    "slot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="selections",
                        to="teacher_app.courseannouncementslot",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcement_slot_selections",
                        to="admin_app.profile",
                    ),
                ),
            ],
            options={
                "ordering": ("created_at",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("announcement", "student"),
                        name="one_slot_per_student_per_announcement",
                    ),
                ],
            },
        ),
    ]
