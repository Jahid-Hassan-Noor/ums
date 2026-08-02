import django.db.models.deletion
from django.db import migrations, models


def backfill_teacher_assignments(apps, schema_editor):
    Teacher = apps.get_model("teacher_app", "Teacher")
    TeacherScopeAssignment = apps.get_model("teacher_app", "TeacherScopeAssignment")

    for teacher in Teacher.objects.exclude(school=None):
        TeacherScopeAssignment.objects.get_or_create(
            teacher=teacher.profile,
            school=teacher.school,
            defaults={"is_primary": True},
        )
    for teacher in Teacher.objects.filter(school=None).exclude(center=None):
        TeacherScopeAssignment.objects.get_or_create(
            teacher=teacher.profile,
            center=teacher.center,
            defaults={"is_primary": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0026_courseoffering_eligible_schools"),
        ("teacher_app", "0007_remove_teacher_program"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeacherScopeAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_primary", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "center",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="admin_app.center"),
                ),
                (
                    "school",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="admin_app.school"),
                ),
                (
                    "teacher",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="teacher_scope_assignments", to="admin_app.profile"),
                ),
            ],
            options={
                "ordering": ("-is_primary", "school__name", "center__name"),
                "constraints": [
                    models.UniqueConstraint(condition=models.Q(("school__isnull", False)), fields=("teacher", "school"), name="unique_teacher_school_assignment"),
                    models.UniqueConstraint(condition=models.Q(("center__isnull", False)), fields=("teacher", "center"), name="unique_teacher_center_assignment"),
                    models.UniqueConstraint(condition=models.Q(("is_active", True), ("is_primary", True)), fields=("teacher",), name="one_primary_teacher_scope_assignment"),
                ],
            },
        ),
        migrations.RunPython(backfill_teacher_assignments, migrations.RunPython.noop),
    ]
