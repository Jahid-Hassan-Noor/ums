from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("technician_app", "0005_adopt_election_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="helpdeskticket",
            name="category",
            field=models.CharField(max_length=40),
        ),
    ]
