from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0033_profile_admin_proxy_state"),
        ("notifications_package", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="Notification"),
                migrations.CreateModel(
                    name="Notification",
                    fields=[],
                    options={
                        "proxy": True,
                        "indexes": [],
                        "constraints": [],
                    },
                    bases=("notifications_package.notification",),
                ),
            ],
        ),
    ]
