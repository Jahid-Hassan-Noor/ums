from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0001_initial"),
        ("admin_app", "0032_add_hr_role"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="Admin"),
                migrations.DeleteModel(name="Profile"),
                migrations.CreateModel(
                    name="Profile",
                    fields=[],
                    options={
                        "proxy": True,
                        "indexes": [],
                        "constraints": [],
                    },
                    bases=("auth_app.profile",),
                ),
                migrations.CreateModel(
                    name="Admin",
                    fields=[],
                    options={
                        "proxy": True,
                        "verbose_name": "Admin",
                        "verbose_name_plural": "Admins",
                        "indexes": [],
                        "constraints": [],
                    },
                    bases=("auth_app.admin",),
                ),
            ],
        ),
    ]
