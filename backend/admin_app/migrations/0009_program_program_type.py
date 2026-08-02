from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0008_hostel_hostelroom"),
    ]

    operations = [
        migrations.AddField(
            model_name="program",
            name="program_type",
            field=models.CharField(
                choices=[
                    ("academic", "Academic program"),
                    ("center_program", "Centre program"),
                ],
                default="academic",
                max_length=30,
            ),
        ),
    ]
