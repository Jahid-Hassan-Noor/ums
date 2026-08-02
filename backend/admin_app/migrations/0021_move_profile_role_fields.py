from django.db import migrations


ROLE_MODELS = {
    "student": ("student_app", "Student", "student_id"),
    "teacher": ("teacher_app", "Teacher", "teacher_id"),
    "executive": ("executive_app", "Executive", "executive_id"),
    "librarian": ("librarian_app", "Librarian", "librarian_id"),
    "caterer": ("caterer_app", "Caterer", "caterer_id"),
    "technician": ("technician_app", "Technician", "technician_id"),
    "admin": ("admin_app", "Admin", "admin_id"),
    "applicant": ("applicant_app", "Applicant", "applicant_id"),
}

ORGANIZATION_FIELDS = ("school", "center", "department", "unit", "program")
STAFF_ROLES = {"teacher", "executive", "librarian", "caterer", "technician", "admin"}


def move_profile_fields_to_role_models(apps, schema_editor):
    Profile = apps.get_model("admin_app", "Profile")

    for profile in Profile.objects.all().iterator():
        app_label, model_name, identifier_field = ROLE_MODELS[profile.role]
        Detail = apps.get_model(app_label, model_name)
        detail, _created = Detail.objects.get_or_create(profile_id=profile.id)
        changed_fields = []

        source_identifier = (
            profile.student_id
            if profile.role == "student"
            else profile.staff_id or profile.student_id
        )
        if source_identifier and not getattr(detail, identifier_field):
            setattr(detail, identifier_field, source_identifier)
            changed_fields.append(identifier_field)

        if profile.role != "applicant":
            for field_name in ORGANIZATION_FIELDS:
                source_id = getattr(profile, f"{field_name}_id")
                if source_id and not getattr(detail, f"{field_name}_id"):
                    setattr(detail, f"{field_name}_id", source_id)
                    changed_fields.append(field_name)

        if profile.role in STAFF_ROLES and profile.designation and not detail.designation:
            detail.designation = profile.designation
            changed_fields.append("designation")

        if changed_fields:
            detail.save(update_fields=changed_fields)


def restore_profile_fields(apps, schema_editor):
    Profile = apps.get_model("admin_app", "Profile")

    for profile in Profile.objects.all().iterator():
        app_label, model_name, identifier_field = ROLE_MODELS[profile.role]
        Detail = apps.get_model(app_label, model_name)
        detail = Detail.objects.filter(profile_id=profile.id).first()
        if not detail:
            continue

        if profile.role == "student":
            profile.student_id = getattr(detail, identifier_field)
        else:
            profile.staff_id = getattr(detail, identifier_field)

        if profile.role != "applicant":
            for field_name in ORGANIZATION_FIELDS:
                setattr(profile, f"{field_name}_id", getattr(detail, f"{field_name}_id"))

        if profile.role in STAFF_ROLES:
            profile.designation = detail.designation

        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0020_role_admin_fields"),
        ("applicant_app", "0005_applicant_applicant_id"),
        ("caterer_app", "0004_remove_caterer_staff_id_caterer_caterer_id_and_more"),
        ("executive_app", "0005_remove_executive_staff_id_executive_center_and_more"),
        ("librarian_app", "0003_remove_librarian_staff_id_librarian_center_and_more"),
        ("student_app", "0008_student_center_student_department_student_program_and_more"),
        ("teacher_app", "0006_remove_teacher_staff_id_teacher_center_and_more"),
        ("technician_app", "0002_remove_technician_staff_id_technician_center_and_more"),
    ]

    operations = [
        migrations.RunPython(move_profile_fields_to_role_models, restore_profile_fields),
        migrations.RemoveField(model_name="profile", name="center"),
        migrations.RemoveField(model_name="profile", name="department"),
        migrations.RemoveField(model_name="profile", name="designation"),
        migrations.RemoveField(model_name="profile", name="program"),
        migrations.RemoveField(model_name="profile", name="school"),
        migrations.RemoveField(model_name="profile", name="staff_id"),
        migrations.RemoveField(model_name="profile", name="student_id"),
        migrations.RemoveField(model_name="profile", name="unit"),
    ]
