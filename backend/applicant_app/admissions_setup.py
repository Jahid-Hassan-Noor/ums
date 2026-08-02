from copy import deepcopy

from django.core.exceptions import ValidationError
from django.utils.text import slugify

from admin_app.models import SystemSetting
from applicant_app import models


SETTING_KEY = "portal.admissions_setup"

DETAIL_FIELD_OPTIONS = [
    {"value": "personal.first_name", "label": "First name", "section": "Personal information"},
    {"value": "personal.last_name", "label": "Last name", "section": "Personal information"},
    {"value": "personal.email", "label": "Email address", "section": "Personal information"},
    {"value": "personal.phone", "label": "Contact number", "section": "Personal information"},
    {"value": "personal.identity_number", "label": "Identity card/passport number", "section": "Personal information"},
    {"value": "personal.country", "label": "Country of residence", "section": "Personal information"},
    {"value": "personal.nationality", "label": "Nationality", "section": "Personal information"},
    {"value": "academic.highest_qualification", "label": "Highest qualification", "section": "Academic information"},
    {"value": "academic.institution_name", "label": "Previous institution name", "section": "Academic information"},
    {"value": "academic.graduation_year", "label": "Graduation year", "section": "Academic information"},
    {"value": "academic.cgpa", "label": "CGPA or equivalent", "section": "Academic information"},
    {"value": "academic.english_proficiency", "label": "English proficiency", "section": "Academic information"},
]

DEFAULT_REQUIRED_DETAIL_FIELDS = [
    "personal.first_name",
    "personal.last_name",
    "personal.email",
    "personal.phone",
    "personal.identity_number",
    "personal.country",
    "personal.nationality",
    "academic.highest_qualification",
    "academic.institution_name",
]

DEFAULT_ADMISSIONS_SETUP = {
    "required_documents": [],
    "required_detail_fields": DEFAULT_REQUIRED_DETAIL_FIELDS,
    "custom_questions": [],
    "scholarship_enabled": True,
}


def detail_field_options():
    return deepcopy(DETAIL_FIELD_OPTIONS)


def document_type_options():
    return [
        {"value": value, "label": label}
        for value, label in models.ApplicationDocument.DOCUMENT_TYPE_CHOICES
    ]


def detail_field_label(field_name):
    for option in DETAIL_FIELD_OPTIONS:
        if option["value"] == field_name:
            return option["label"]
    return field_name


def _unique_values(values, allowed):
    normalized = []
    for value in values or []:
        key = str(value or "").strip()
        if key and key in allowed and key not in normalized:
            normalized.append(key)
    return normalized


def _question_id(label, existing):
    base = slugify(label).replace("-", "_") or "question"
    candidate = base[:48]
    counter = 2
    while candidate in existing:
        suffix = f"_{counter}"
        candidate = f"{base[:48 - len(suffix)]}{suffix}"
        counter += 1
    existing.add(candidate)
    return candidate


def normalize_admissions_setup(payload):
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValidationError({"detail": "Admissions setup must be an object."})

    current = deepcopy(DEFAULT_ADMISSIONS_SETUP)
    current.update(payload)

    allowed_documents = {value for value, _label in models.ApplicationDocument.DOCUMENT_TYPE_CHOICES}
    allowed_fields = {option["value"] for option in DETAIL_FIELD_OPTIONS}

    questions = []
    used_ids = set()
    for raw_question in current.get("custom_questions") or []:
        if not isinstance(raw_question, dict):
            continue
        label = str(raw_question.get("label") or "").strip()
        if not label:
            continue
        if len(label) > 120:
            raise ValidationError({"custom_questions": "Question labels must be 120 characters or fewer."})
        help_text = str(raw_question.get("help_text") or "").strip()
        if len(help_text) > 240:
            raise ValidationError({"custom_questions": "Question help text must be 240 characters or fewer."})
        submitted_id = str(raw_question.get("id") or "").strip()
        question_id = submitted_id if submitted_id and submitted_id not in used_ids else _question_id(label, used_ids)
        used_ids.add(question_id)
        questions.append(
            {
                "id": question_id[:60],
                "label": label,
                "help_text": help_text,
                "required": bool(raw_question.get("required", False)),
            }
        )
        if len(questions) >= 12:
            break

    return {
        "required_documents": _unique_values(current.get("required_documents"), allowed_documents),
        "required_detail_fields": _unique_values(current.get("required_detail_fields"), allowed_fields),
        "custom_questions": questions,
        "scholarship_enabled": bool(current.get("scholarship_enabled", True)),
    }


def admissions_setup():
    record = SystemSetting.objects.filter(key=SETTING_KEY).first()
    value = record.value if record and isinstance(record.value, dict) else {}
    return normalize_admissions_setup(value)


def update_admissions_setup(payload, updated_by=None):
    normalized = normalize_admissions_setup(payload)
    SystemSetting.objects.update_or_create(
        key=SETTING_KEY,
        defaults={
            "value": normalized,
            "description": "Admissions form questions, required documents, and scholarship controls.",
            "is_public": True,
            "updated_by": updated_by,
        },
    )
    return normalized


def admissions_setup_payload():
    return {
        "settings": admissions_setup(),
        "detail_fields": detail_field_options(),
        "document_types": document_type_options(),
    }
