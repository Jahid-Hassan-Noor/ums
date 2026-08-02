from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0026_courseoffering_eligible_schools"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="classmeeting",
            name="source_column",
        ),
        migrations.RemoveField(
            model_name="classmeeting",
            name="source_job",
        ),
        migrations.RemoveField(
            model_name="classmeeting",
            name="source_row",
        ),
        migrations.RemoveField(
            model_name="classmeeting",
            name="source_sheet",
        ),
        migrations.RemoveField(
            model_name="classmeeting",
            name="source_text",
        ),
        migrations.DeleteModel(
            name="TimetableImportIssue",
        ),
        migrations.DeleteModel(
            name="TimetableImportRow",
        ),
        migrations.DeleteModel(
            name="TimetableImportJob",
        ),
        migrations.AlterField(
            model_name="importjob",
            name="import_type",
            field=models.CharField(
                choices=[
                    ("users", "Users"),
                    ("results", "Results"),
                    ("public_content", "Public Content"),
                ],
                max_length=40,
            ),
        ),
    ]
