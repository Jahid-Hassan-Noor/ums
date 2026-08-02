from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0006_merge_20260525_1604"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="center",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="admin_app.center",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="admin_app.school",
            ),
        ),
        migrations.AddField(
            model_name="classmeeting",
            name="class_type",
            field=models.CharField(
                choices=[
                    ("lecture", "Lecture Class"),
                    ("lab", "Lab Class"),
                ],
                default="lecture",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="classmeeting",
            name="meeting_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="classmeeting",
            name="recurring_meeting",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="single_week_adjustments",
                to="admin_app.classmeeting",
            ),
        ),
    ]
