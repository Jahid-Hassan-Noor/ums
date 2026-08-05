from django.core.exceptions import ValidationError

from admin_app import models
from admin_app.settings_registry import setting_values


SPECIAL_OWNER_ROLES = {
    models.Profile.ROLE_LIBRARIAN,
    models.Profile.ROLE_CATERER,
    models.Profile.ROLE_TECHNICIAN,
}


ROLE_OWNER_SETTINGS = {
    models.Profile.ROLE_LIBRARIAN: {
        "label": "librarian",
        "center_code": "librarian_default_center_code",
        "unit_code": "librarian_default_unit_code",
        "requires": "a library center or unit",
    },
    models.Profile.ROLE_CATERER: {
        "label": "caterer",
        "center_code": "caterer_default_center_code",
        "unit_code": "caterer_default_unit_code",
        "requires": "a dining/canteen center or unit",
    },
    models.Profile.ROLE_TECHNICIAN: {
        "label": "technician",
        "department_code": "technician_default_department_code",
        "unit_code": "technician_default_unit_code",
        "requires": "a service desk department or unit",
    },
}


def _active_by_code(model, code, label):
    normalized = str(code or "").strip()
    if not normalized:
        return None
    record = model.objects.filter(code__iexact=normalized, is_active=True).first()
    if not record:
        raise ValidationError(
            {
                "role": (
                    f"The configured {label} code '{normalized}' does not match "
                    "an active record."
                )
            }
        )
    return record


def _coerce_scope_from_unit(*, school, center, department, unit):
    if not unit:
        return school, center, department

    if school and unit.school_id and unit.school_id != school.id:
        raise ValidationError(
            {"unit_id": "Selected unit does not belong to the selected school."}
        )
    if center and unit.center_id and unit.center_id != center.id:
        raise ValidationError(
            {"unit_id": "Selected unit does not belong to the selected center."}
        )
    if department and unit.department_id and unit.department_id != department.id:
        raise ValidationError(
            {"unit_id": "Selected unit does not belong to the selected department."}
        )

    if not school and unit.school_id:
        school = unit.school
    if not center and unit.center_id:
        center = unit.center
    if not department and unit.department_id:
        department = unit.department
    return school, center, department


def _coerce_scope_from_department(*, school, center, department):
    if not department:
        return school, center

    if school and department.school_id and department.school_id != school.id:
        raise ValidationError(
            {
                "department_id": (
                    "Selected department does not belong to the selected school."
                )
            }
        )
    if center and department.center_id and department.center_id != center.id:
        raise ValidationError(
            {
                "department_id": (
                    "Selected department does not belong to the selected center."
                )
            }
        )
    if not school and department.school_id:
        school = department.school
    if not center and department.center_id:
        center = department.center
    return school, center


def _configured_owner(role):
    config = ROLE_OWNER_SETTINGS[role]
    values = setting_values("roles")
    unit = _active_by_code(
        models.Unit,
        values.get(config.get("unit_code")),
        f"{config['label']} owner unit",
    )
    center = _active_by_code(
        models.Center,
        values.get(config.get("center_code")),
        f"{config['label']} owner center",
    )
    department = _active_by_code(
        models.Department,
        values.get(config.get("department_code")),
        f"{config['label']} owner department",
    )
    return center, unit, department


def resolve_role_ownership(role, *, school=None, center=None, unit=None, department=None):
    if role not in SPECIAL_OWNER_ROLES:
        return {
            "school": school,
            "center": center,
            "unit": unit,
            "department": department,
        }

    config = ROLE_OWNER_SETTINGS[role]
    if not any((school, center, unit, department)):
        center, unit, department = _configured_owner(role)

    school, center, department = _coerce_scope_from_unit(
        school=school,
        center=center,
        department=department,
        unit=unit,
    )
    school, center = _coerce_scope_from_department(
        school=school,
        center=center,
        department=department,
    )

    if school and center:
        raise ValidationError({"school_id": "Assign only one school or center."})

    has_required_owner = bool(unit or center or school)
    if role == models.Profile.ROLE_TECHNICIAN:
        has_required_owner = bool(unit or department or center or school)

    if not has_required_owner:
        raise ValidationError(
            {
                "role": (
                    f"Configure {config['requires']} in Settings > Roles, or "
                    "select an owner while creating this account."
                )
            }
        )

    return {
        "school": school,
        "center": center,
        "unit": unit,
        "department": department,
    }


def _object_from_payload(model, payload, key, label, current=None):
    if key not in payload:
        return current
    raw_value = payload.get(key)
    if raw_value in ("", None):
        return None
    record = model.objects.filter(pk=raw_value, is_active=True).first()
    if not record:
        raise ValidationError({key: f"Select a valid active {label}."})
    return record


def resolve_role_ownership_from_payload(role, payload, *, current_profile=None):
    school = current_profile.school if current_profile else None
    center = current_profile.center if current_profile else None
    unit = current_profile.unit if current_profile else None
    department = current_profile.department if current_profile else None

    school = _object_from_payload(models.School, payload, "school_id", "school", school)
    center = _object_from_payload(models.Center, payload, "center_id", "center", center)
    unit = _object_from_payload(models.Unit, payload, "unit_id", "unit", unit)
    department = _object_from_payload(
        models.Department,
        payload,
        "department_id",
        "department",
        department,
    )
    return resolve_role_ownership(
        role,
        school=school,
        center=center,
        unit=unit,
        department=department,
    )
