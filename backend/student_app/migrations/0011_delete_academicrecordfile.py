# Generated manually to remove the standalone academic records backend surface.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("student_app", "0010_examvenueallocation_exam_constraints"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AcademicRecordFile",
        ),
    ]
