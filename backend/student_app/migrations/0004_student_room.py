from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("student_app", "0003_student"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="room",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
