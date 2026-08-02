from uuid import uuid4

from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.audit import set_audit_details
from admin_app.models import Profile, SystemSetting
from auth_app.permissions import IsAdminRole
from admin_app.settings_registry import (
    SETTINGS_SECTIONS,
    LEGACY_SETTINGS_KEY_PREFIX,
    SETTINGS_KEY_PREFIX,
    all_settings,
    invalidate_settings_cache,
    section_payload,
    section_from_setting_key,
    setting_key,
    validate_section_values,
)
from core.upload_security import image_file_extension, validate_image_upload
from notifications_package.service import notify_profile


class AdminSettings(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request):
        values = all_settings()
        records = {
            section_from_setting_key(record.key): record
            for record in SystemSetting.objects.filter(
                key__startswith=SETTINGS_KEY_PREFIX
            ).select_related("updated_by__user")
        }
        for record in SystemSetting.objects.filter(
            key__startswith=LEGACY_SETTINGS_KEY_PREFIX
        ).select_related("updated_by__user"):
            records.setdefault(section_from_setting_key(record.key), record)
        return Response(
            {
                "title": "Settings",
                "section": "admin",
                "sections": [
                    section_payload(section, values[section], records.get(section))
                    for section in SETTINGS_SECTIONS
                ],
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request):
        section = str(request.data.get("section") or "").strip()
        reason = str(request.data.get("reason") or "").strip()
        current_sections = all_settings()
        if section not in current_sections:
            return Response({"section": "Unknown settings section."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            normalized = validate_section_values(
                section,
                request.data.get("values"),
                current_sections[section],
            )
        except ValidationError as error:
            return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)

        fields = SETTINGS_SECTIONS[section]["fields"]
        changes = [
            {
                "setting": f"{section}.{name}",
                "previous_value": current_sections[section].get(name),
                "new_value": normalized.get(name),
            }
            for name in fields
            if current_sections[section].get(name) != normalized.get(name)
        ]
        high_impact = any(
            fields[change["setting"].split(".", 1)[1]].get("high_impact", False)
            for change in changes
        )
        if high_impact and not reason:
            return Response(
                {"reason": "A reason is required for high-impact settings changes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record, _created = SystemSetting.objects.update_or_create(
            key=setting_key(section),
            defaults={
                "value": normalized,
                "description": SETTINGS_SECTIONS[section]["description"],
                "updated_by": request.user.profile,
            },
        )
        invalidate_settings_cache()
        set_audit_details(
            request,
            {
                "changes": changes,
                "reason": reason,
                "high_impact": high_impact,
            },
        )
        return Response(
            {
                "message": (
                    f"{SETTINGS_SECTIONS[section]['title']} updated successfully."
                    if changes
                    else "No settings values changed."
                ),
                "section": section_payload(section, normalized, record),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        action = request.data.get("action")
        if action == "upload_image":
            return self._upload_image(request)
        if action != "test_notification":
            return Response({"detail": "Unknown settings action."}, status=status.HTTP_400_BAD_REQUEST)
        values = all_settings()["notifications"]
        profile = Profile.objects.filter(user=request.user, role=Profile.ROLE_ADMIN).first()
        if not profile:
            return Response({"detail": "Admin profile not found."}, status=status.HTTP_404_NOT_FOUND)
        notify_profile(
            profile,
            actor=profile,
            event_type="settings.test_notification",
            verb=f"Test notification from {values['sender_display_name']}",
            data={"settings_test": True},
            url="/admin/settings",
        )
        return Response({"message": "Test notification created for your admin account."})

    @transaction.atomic
    def _upload_image(self, request):
        section = str(request.data.get("section") or "").strip()
        field_name = str(request.data.get("field") or "").strip()
        reason = str(request.data.get("reason") or "").strip()
        upload = request.FILES.get("file")
        current_sections = all_settings()

        if section not in current_sections:
            return Response({"section": "Unknown settings section."}, status=status.HTTP_400_BAD_REQUEST)

        fields = SETTINGS_SECTIONS[section]["fields"]
        field = fields.get(field_name)
        if not field:
            return Response({"field": "Unknown settings field."}, status=status.HTTP_400_BAD_REQUEST)
        if field["type"] != "image":
            return Response(
                {"field": "This setting does not accept image uploads."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload is None:
            return Response({"file": "Choose an image to upload."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_image_upload(upload, field_label=field["label"])
        except ValidationError as error:
            return Response({"file": " ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)

        extension = image_file_extension(upload)
        storage_path = (
            f"settings/images/{section}/{field_name}/{uuid4().hex}.{extension}"
        )
        saved_path = default_storage.save(storage_path, upload)
        image_url = default_storage.url(saved_path)

        try:
            normalized = validate_section_values(
                section,
                {field_name: image_url},
                current_sections[section],
            )
        except ValidationError as error:
            default_storage.delete(saved_path)
            return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)

        change = {
            "setting": f"{section}.{field_name}",
            "previous_value": current_sections[section].get(field_name),
            "new_value": normalized.get(field_name),
        }
        record, _created = SystemSetting.objects.update_or_create(
            key=setting_key(section),
            defaults={
                "value": normalized,
                "description": SETTINGS_SECTIONS[section]["description"],
                "updated_by": request.user.profile,
            },
        )
        invalidate_settings_cache()
        set_audit_details(
            request,
            {
                "changes": [change],
                "reason": reason,
                "high_impact": False,
            },
        )

        return Response(
            {
                "message": f"{field['label']} uploaded successfully.",
                "url": image_url,
                "section": section_payload(section, normalized, record),
            },
            status=status.HTTP_200_OK,
        )
