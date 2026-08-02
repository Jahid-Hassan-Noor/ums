from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("executive_app", "0006_remove_executive_program"),
    ]

    operations = [
        migrations.DeleteModel(
            name="RegistrationDecision",
        ),
    ]
