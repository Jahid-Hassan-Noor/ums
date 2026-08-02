from copy import deepcopy

from django.core.exceptions import ValidationError

from admin_app.models import SystemSetting


SETTING_KEY = "hostel.student_life"

DEFAULT_STUDENT_LIFE = {
    "emergency_contacts": [],
    "warden_schedule": [],
}

CONTACT_FIELDS = ("label", "phone", "email", "available_hours", "notes")
SCHEDULE_FIELDS = ("day", "time_range", "warden_name", "phone", "location", "notes")
MAX_ITEMS = 30
MAX_TEXT_LENGTH = 255


def _clean_text(value, field_name, section, row_number, max_length=MAX_TEXT_LENGTH):
    text = str(value or "").strip()
    if len(text) > max_length:
        raise ValidationError(
            {section: f"Row {row_number} {field_name.replace('_', ' ')} is too long."}
        )
    return text


def _normalise_list(value, section):
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValidationError({section: "Expected a list of rows."})
    if len(value) > MAX_ITEMS:
        raise ValidationError({section: f"Keep this list to {MAX_ITEMS} rows or fewer."})
    return value


def _normalise_contact(raw, index):
    if not isinstance(raw, dict):
        raise ValidationError({"emergency_contacts": f"Row {index} must be an object."})

    item = {
        field: _clean_text(raw.get(field), field, "emergency_contacts", index)
        for field in CONTACT_FIELDS
    }
    if not any(item.values()):
        return None
    if not item["label"]:
        raise ValidationError({"emergency_contacts": f"Row {index} needs a contact name."})
    if not item["phone"] and not item["email"]:
        raise ValidationError(
            {"emergency_contacts": f"Row {index} needs a phone number or email address."}
        )
    return item


def _normalise_schedule(raw, index):
    if not isinstance(raw, dict):
        raise ValidationError({"warden_schedule": f"Row {index} must be an object."})

    item = {
        field: _clean_text(raw.get(field), field, "warden_schedule", index)
        for field in SCHEDULE_FIELDS
    }
    if not any(item.values()):
        return None
    if not item["day"]:
        raise ValidationError({"warden_schedule": f"Row {index} needs a day or date."})
    if not item["time_range"]:
        raise ValidationError({"warden_schedule": f"Row {index} needs a time range."})
    if not item["warden_name"]:
        raise ValidationError({"warden_schedule": f"Row {index} needs a warden name."})
    return item


def normalise_student_life_payload(raw_payload):
    if raw_payload in (None, ""):
        raw_payload = {}
    if not isinstance(raw_payload, dict):
        raise ValidationError({"student_life": "Expected an object."})

    contacts = []
    for index, raw in enumerate(
        _normalise_list(raw_payload.get("emergency_contacts"), "emergency_contacts"),
        start=1,
    ):
        item = _normalise_contact(raw, index)
        if item:
            contacts.append(item)

    schedule = []
    for index, raw in enumerate(
        _normalise_list(raw_payload.get("warden_schedule"), "warden_schedule"),
        start=1,
    ):
        item = _normalise_schedule(raw, index)
        if item:
            schedule.append(item)

    return {
        "emergency_contacts": contacts,
        "warden_schedule": schedule,
    }


def _profile_name(profile):
    if not profile:
        return ""
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def hostel_student_life_payload():
    record = (
        SystemSetting.objects.filter(key=SETTING_KEY)
        .select_related("updated_by__user")
        .first()
    )
    value = deepcopy(DEFAULT_STUDENT_LIFE)
    if record and isinstance(record.value, dict):
        try:
            value = normalise_student_life_payload(record.value)
        except ValidationError:
            value = deepcopy(DEFAULT_STUDENT_LIFE)

    return {
        **value,
        "updated_at": record.updated_at.isoformat() if record else None,
        "updated_by": _profile_name(record.updated_by) if record else "",
    }


def save_hostel_student_life(raw_payload, updated_by):
    value = normalise_student_life_payload(raw_payload)
    SystemSetting.objects.update_or_create(
        key=SETTING_KEY,
        defaults={
            "value": value,
            "description": "Student-facing hostel emergency contacts and warden schedule.",
            "is_public": True,
            "updated_by": updated_by,
        },
    )
    return hostel_student_life_payload()
