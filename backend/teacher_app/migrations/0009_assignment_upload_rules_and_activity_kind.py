from django.db import migrations, models


def backfill_accepted_file_types(apps, schema_editor):
    Assignment = apps.get_model("teacher_app", "Assignment")
    for assignment in Assignment.objects.all().iterator():
        assignment.accepted_file_types = [assignment.accepted_file_type]
        assignment.save(update_fields=["accepted_file_types"])


class Migration(migrations.Migration):

    dependencies = [
        ("teacher_app", "0008_teacherscopeassignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="activity_kind",
            field=models.CharField(
                choices=[("assignment", "Assignment"), ("lab_activity", "Lab activity")],
                default="assignment",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="assignment",
            name="accepted_file_type",
            field=models.CharField(
                choices=[
                    ("doc", "DOC/DOCX"),
                    ("pdf", "PDF"),
                    ("zip", "ZIP"),
                    ("presentation", "PPT/PPTX"),
                    ("image", "JPG/JPEG/PNG"),
                    ("spreadsheet", "XLS/XLSX/CSV"),
                ],
                default="pdf",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="assignment",
            name="accepted_file_types",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="assignment",
            name="max_file_size_mb",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.RunPython(backfill_accepted_file_types, migrations.RunPython.noop),
    ]
