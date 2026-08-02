from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0025_semester_course_offering_closes_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseoffering",
            name="eligible_schools",
            field=models.ManyToManyField(
                blank=True,
                related_name="eligible_course_offerings",
                to="admin_app.school",
            ),
        ),
    ]
