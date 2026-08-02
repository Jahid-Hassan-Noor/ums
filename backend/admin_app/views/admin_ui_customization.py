from copy import deepcopy
from uuid import uuid4

from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.audit import set_audit_details
from admin_app.models import SystemSetting
from auth_app.permissions import IsAdminRole
from admin_app.settings_registry import (
    UI_CUSTOMIZATION_DEFINITION,
    UI_CUSTOMIZATION_DEFAULTS,
    _normalize_value,
    invalidate_settings_cache,
    public_settings_payload,
    setting_key,
)
from core.upload_security import image_file_extension, validate_image_upload


UI_SECTION = "ui_customization"
FIELDS = UI_CUSTOMIZATION_DEFINITION["fields"]


def _current_ui_values():
    try:
        record = SystemSetting.objects.get(key=setting_key(UI_SECTION))
        if isinstance(record.value, dict):
            return {
                key: record.value.get(key, default)
                for key, default in UI_CUSTOMIZATION_DEFAULTS.items()
            }
    except SystemSetting.DoesNotExist:
        pass
    return dict(UI_CUSTOMIZATION_DEFAULTS)


def _ui_section_payload(values, record=None):
    return {
        "key": UI_SECTION,
        "title": UI_CUSTOMIZATION_DEFINITION["title"],
        "description": UI_CUSTOMIZATION_DEFINITION["description"],
        "fields": [
            {"key": key, **deepcopy(config)}
            for key, config in FIELDS.items()
        ],
        "values": deepcopy(values),
        "updated_at": record.updated_at.isoformat() if record else None,
        "updated_by": (
            record.updated_by.user.get_full_name().strip()
            or record.updated_by.user.username
            if record and record.updated_by_id
            else ""
        ),
    }


def _validate_ui_values(submitted, current):
    if not isinstance(submitted, dict):
        raise ValidationError({"values": "Settings values must be an object."})
    unknown = sorted(set(submitted) - set(FIELDS))
    if unknown:
        raise ValidationError(
            {"values": f"Unknown setting(s): {', '.join(unknown)}."}
        )
    normalized = dict(current)
    for name, value in submitted.items():
        normalized[name] = _normalize_value(name, value, FIELDS[name])
    return normalized


class AdminUiCustomization(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request):
        record = (
            SystemSetting.objects.filter(key=setting_key(UI_SECTION))
            .select_related("updated_by__user")
            .first()
        )
        return Response(
            {
                "section": _ui_section_payload(
                    _current_ui_values(), record
                ),
                "public_payload": public_settings_payload(),
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request):
        reason = str(request.data.get("reason") or "").strip()
        current = _current_ui_values()

        try:
            normalized = _validate_ui_values(
                request.data.get("values"), current
            )
        except ValidationError as error:
            return Response(
                error.message_dict, status=status.HTTP_400_BAD_REQUEST
            )

        changes = [
            {
                "setting": f"{UI_SECTION}.{name}",
                "previous_value": current.get(name),
                "new_value": normalized.get(name),
            }
            for name in FIELDS
            if current.get(name) != normalized.get(name)
        ]

        record, _created = SystemSetting.objects.update_or_create(
            key=setting_key(UI_SECTION),
            defaults={
                "value": normalized,
                "description": UI_CUSTOMIZATION_DEFINITION["description"],
                "updated_by": request.user.profile,
            },
        )
        invalidate_settings_cache()
        set_audit_details(
            request,
            {
                "changes": changes,
                "reason": reason,
                "high_impact": False,
            },
        )
        return Response(
            {
                "message": (
                    f"{UI_CUSTOMIZATION_DEFINITION['title']} updated successfully."
                    if changes
                    else "No settings values changed."
                ),
                "section": _ui_section_payload(normalized, record),
                "public_payload": public_settings_payload(),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        action = request.data.get("action")
        if action == "upload_image":
            return self._upload_image(request)
        if action == "restore_defaults":
            return self._restore_defaults(request)
        return Response(
            {"detail": "Unknown action."}, status=status.HTTP_400_BAD_REQUEST
        )

    @transaction.atomic
    def _restore_defaults(self, request):
        reason = str(request.data.get("reason") or "").strip()
        normalized = dict(UI_CUSTOMIZATION_DEFAULTS)
        record, _created = SystemSetting.objects.update_or_create(
            key=setting_key(UI_SECTION),
            defaults={
                "value": normalized,
                "description": UI_CUSTOMIZATION_DEFINITION["description"],
                "updated_by": request.user.profile,
            },
        )
        invalidate_settings_cache()
        set_audit_details(
            request,
            {
                "changes": [
                    {
                        "setting": f"{UI_SECTION}.{name}",
                        "previous_value": None,
                        "new_value": value,
                    }
                    for name, value in normalized.items()
                ],
                "reason": reason or "Restored to default values",
                "high_impact": False,
            },
        )
        return Response(
            {
                "message": "UI customization restored to default values.",
                "section": _ui_section_payload(normalized, record),
                "public_payload": public_settings_payload(),
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def _upload_image(self, request):
        field_name = str(request.data.get("field") or "").strip()
        reason = str(request.data.get("reason") or "").strip()
        upload = request.FILES.get("file")
        current = _current_ui_values()

        field = FIELDS.get(field_name)
        if not field:
            return Response(
                {"field": "Unknown settings field."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if field["type"] != "image":
            return Response(
                {"field": "This setting does not accept image uploads."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload is None:
            return Response(
                {"file": "Choose an image to upload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_image_upload(upload, field_label=field["label"])
        except ValidationError as error:
            return Response(
                {"file": " ".join(error.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = image_file_extension(upload)
        storage_path = (
            f"settings/images/{UI_SECTION}/{field_name}/{uuid4().hex}.{extension}"
        )
        saved_path = default_storage.save(storage_path, upload)
        image_url = default_storage.url(saved_path)

        try:
            normalized = _validate_ui_values(
                {field_name: image_url}, current
            )
        except ValidationError as error:
            default_storage.delete(saved_path)
            return Response(
                error.message_dict, status=status.HTTP_400_BAD_REQUEST
            )

        record, _created = SystemSetting.objects.update_or_create(
            key=setting_key(UI_SECTION),
            defaults={
                "value": normalized,
                "description": UI_CUSTOMIZATION_DEFINITION["description"],
                "updated_by": request.user.profile,
            },
        )
        invalidate_settings_cache()
        set_audit_details(
            request,
            {
                "changes": [
                    {
                        "setting": f"{UI_SECTION}.{field_name}",
                        "previous_value": current.get(field_name),
                        "new_value": normalized.get(field_name),
                    }
                ],
                "reason": reason,
                "high_impact": False,
            },
        )

        return Response(
            {
                "message": f"{field['label']} uploaded successfully.",
                "url": image_url,
                "section": _ui_section_payload(normalized, record),
                "public_payload": public_settings_payload(),
            },
            status=status.HTTP_200_OK,
        )
