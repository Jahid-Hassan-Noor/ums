from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("technician_app", "0006_helpdeskticket_dynamic_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="election_type",
            field=models.CharField(default="student_council", max_length=80),
        ),
        migrations.AddField(
            model_name="election",
            name="election_type_label",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="election",
            name="constituency_type",
            field=models.CharField(
                choices=[
                    ("university", "University-wide"),
                    ("school", "School"),
                    ("center", "Center"),
                    ("department", "Department"),
                    ("program", "Program"),
                    ("cohort", "Cohort"),
                ],
                default="university",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="election",
            name="constituency_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="election",
            name="constituency_label",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="election",
            name="seat_rules",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="election",
            name="nomination_rules",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="election",
            name="voter_eligibility",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="election",
            name="result_publication_rules",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="electioncandidate",
            name="category",
            field=models.CharField(default="general", max_length=80),
        ),
        migrations.AlterField(
            model_name="vote",
            name="category",
            field=models.CharField(default="general", max_length=80),
        ),
    ]
