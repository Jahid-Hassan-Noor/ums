from django.db import migrations


def create_canteen_admin_unit(apps, schema_editor):
    Center = apps.get_model("admin_app", "Center")
    Unit = apps.get_model("admin_app", "Unit")

    center = Center.objects.filter(code="CSAA").first()
    if not center:
        return

    Unit.objects.update_or_create(
        code="CTN-ADMIN",
        defaults={
            "name": "Canteen Admin",
            "unit_type": "administrative",
            "center": center,
            "school": None,
            "department": None,
            "description": "Canteen administration and student meal allowance operations.",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("caterer_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_canteen_admin_unit, migrations.RunPython.noop),
    ]
