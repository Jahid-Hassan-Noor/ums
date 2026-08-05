from copy import deepcopy
import re
import uuid

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone

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

DEFAULT_DOCUMENT_TYPES = [
    {"value": value, "label": label, "kind": "image" if value in {"passport", "photo"} else "file"}
    for value, label in models.ApplicationDocument.DOCUMENT_TYPE_CHOICES
]

DEFAULT_WORKFLOW_STEPS = [
    {"value": value, "label": label, "enabled": True}
    for value, label in models.AdmissionApplication.STEP_CHOICES
]

DEFAULT_STATUS_OPTIONS = [
    {"value": value, "label": label, "enabled": True}
    for value, label in models.AdmissionApplication.STATUS_CHOICES
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
    "application_number_prefix": "",
    "application_number_format": "{prefix}-{period}-{token}",
    "document_types": DEFAULT_DOCUMENT_TYPES,
    "required_documents": [],
    "required_detail_fields": DEFAULT_REQUIRED_DETAIL_FIELDS,
    "custom_questions": [],
    "scholarship_enabled": True,
    "scholarship_label": "Scholarship Application",
    "workflow_steps": DEFAULT_WORKFLOW_STEPS,
    "status_options": DEFAULT_STATUS_OPTIONS,
}


def detail_field_options():
    return deepcopy(DETAIL_FIELD_OPTIONS)


def document_type_options(setup=None):
    setup = setup or admissions_setup()
    return deepcopy(setup["document_types"])


def document_type_catalog():
    return deepcopy(DEFAULT_DOCUMENT_TYPES)


def workflow_step_options(setup=None):
    setup = setup or admissions_setup()
    return [item for item in setup["workflow_steps"] if item["enabled"]]


def status_options(setup=None):
    setup = setup or admissions_setup()
    return deepcopy(setup["status_options"])


def admission_status_choices(setup=None):
    return [
        (item["value"], item["label"])
        for item in status_options(setup)
        if item["enabled"]
    ]


def document_type_config(document_type, setup=None):
    return next(
        (item for item in document_type_options(setup) if item["value"] == document_type),
        None,
    )


def is_image_document_type(document_type, setup=None):
    config = document_type_config(document_type, setup)
    return bool(config and config.get("kind") == "image")


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


def _normalise_document_value(value):
    value = slugify(str(value or "").strip()).replace("-", "_")
    return value[:50]


def _normalise_document_types(raw_types, required_values):
    catalog = {item["value"]: item for item in DEFAULT_DOCUMENT_TYPES}
    source = raw_types if isinstance(raw_types, list) else DEFAULT_DOCUMENT_TYPES
    normalized = []
    seen = set()
    for raw_item in source:
        if isinstance(raw_item, str):
            raw_item = {"value": raw_item}
        if not isinstance(raw_item, dict):
            continue
        value = _normalise_document_value(raw_item.get("value"))
        if not value or value in seen:
            continue
        catalog_item = catalog.get(value, {})
        label = str(raw_item.get("label") or catalog_item.get("label") or value.replace("_", " ").title()).strip()
        if len(label) > 120:
            raise ValidationError({"document_types": "Document labels must be 120 characters or fewer."})
        kind = str(raw_item.get("kind") or catalog_item.get("kind") or "file").strip().lower()
        if kind not in {"file", "image"}:
            raise ValidationError({"document_types": "Document kind must be file or image."})
        seen.add(value)
        normalized.append(
            {
                "value": value,
                "label": label,
                "kind": kind,
                "required": bool(raw_item.get("required", False)) or value in required_values,
            }
        )
        if len(normalized) >= 30:
            break
    return normalized


def _normalise_workflow_items(raw_items, defaults, field_name):
    source = raw_items if isinstance(raw_items, list) else defaults
    default_by_value = {item["value"]: item for item in defaults}
    normalized = []
    seen = set()
    for raw_item in source:
        if isinstance(raw_item, str):
            raw_item = {"value": raw_item}
        if not isinstance(raw_item, dict):
            continue
        value = str(raw_item.get("value") or "").strip()
        if not value or value in seen or value not in default_by_value:
            continue
        default = default_by_value[value]
        label = str(raw_item.get("label") or default["label"]).strip()
        if len(label) > 120:
            raise ValidationError({field_name: "Workflow labels must be 120 characters or fewer."})
        normalized.append(
            {
                "value": value,
                "label": label,
                "enabled": bool(raw_item.get("enabled", default.get("enabled", True))),
            }
        )
        seen.add(value)
    for default in defaults:
        if default["value"] not in seen:
            normalized.append(deepcopy(default))
    return normalized


def _normalise_number_format(value):
    value = str(value or "{prefix}-{period}-{token}").strip()
    if len(value) > 60:
        raise ValidationError({"application_number_format": "Application number format must be 60 characters or fewer."})
    tokens = set(re.findall(r"\{([a-z_]+)\}", value))
    allowed_tokens = {"prefix", "year", "month", "period", "token"}
    if not value or tokens - allowed_tokens or "{token}" not in value:
        raise ValidationError(
            {
                "application_number_format": (
                    "Use {prefix}, {year}, {month}, {period}, and {token}; "
                    "the format must include {token}."
                )
            }
        )
    return value


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

    allowed_fields = {option["value"] for option in DETAIL_FIELD_OPTIONS}
    requested_documents = {
        _normalise_document_value(value)
        for value in current.get("required_documents") or []
        if _normalise_document_value(value)
    }

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

    document_types = _normalise_document_types(current.get("document_types"), requested_documents)
    document_values = {item["value"] for item in document_types}
    required_documents = [
        item["value"]
        for item in document_types
        if item.get("required") or item["value"] in requested_documents
    ]
    workflow_steps = _normalise_workflow_items(
        current.get("workflow_steps"), DEFAULT_WORKFLOW_STEPS, "workflow_steps"
    )
    scholarship_enabled = bool(current.get("scholarship_enabled", True))
    if not scholarship_enabled:
        for item in workflow_steps:
            if item["value"] == models.AdmissionApplication.STEP_SCHOLARSHIP:
                item["enabled"] = False
    status_items = _normalise_workflow_items(
        current.get("status_options"), DEFAULT_STATUS_OPTIONS, "status_options"
    )
    if not scholarship_enabled:
        for item in status_items:
            if item["value"] == models.AdmissionApplication.STATUS_SCHOLARSHIP_REVIEW:
                item["enabled"] = False
    for required_status in (models.AdmissionApplication.STATUS_DRAFT, models.AdmissionApplication.STATUS_SUBMITTED):
        for item in status_items:
            if item["value"] == required_status:
                item["enabled"] = True

    prefix = str(current.get("application_number_prefix") or "").strip().upper()
    prefix = "".join(character for character in prefix if character.isalnum() or character in {"-", "_"})[:20]
    scholarship_label = str(current.get("scholarship_label") or "Scholarship Application").strip()
    if len(scholarship_label) > 120:
        raise ValidationError({"scholarship_label": "Scholarship label must be 120 characters or fewer."})

    return {
        "application_number_prefix": prefix,
        "application_number_format": _normalise_number_format(current.get("application_number_format")),
        "document_types": document_types,
        "required_documents": [value for value in required_documents if value in document_values],
        "required_detail_fields": _unique_values(current.get("required_detail_fields"), allowed_fields),
        "custom_questions": questions,
        "scholarship_enabled": scholarship_enabled,
        "scholarship_label": scholarship_label,
        "workflow_steps": workflow_steps,
        "status_options": status_items,
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
            "description": "Admissions numbering, form questions, documents, and workflow controls.",
            "is_public": True,
            "updated_by": updated_by,
        },
    )
    return normalized


def admissions_setup_payload():
    setup = admissions_setup()
    return {
        "settings": setup,
        "detail_fields": detail_field_options(),
        "document_types": document_type_options(setup),
        "document_type_options": document_type_catalog(),
        "steps": workflow_step_options(setup),
        "status_options": status_options(setup),
    }


def generate_application_number():
    setup = admissions_setup()
    prefix = setup["application_number_prefix"]
    if not prefix:
        from admin_app.settings_registry import application_number_prefix

        prefix = application_number_prefix()
    now = timezone.now()
    values = {
        "prefix": prefix,
        "year": now.strftime("%Y"),
        "month": now.strftime("%m"),
        "period": now.strftime("%Y%m"),
        "token": uuid.uuid4().hex[:8].upper(),
    }
    return setup["application_number_format"].format(**values)[:40]
