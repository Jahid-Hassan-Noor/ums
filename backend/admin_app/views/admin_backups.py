import logging
import tempfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.http import FileResponse
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.audit import set_audit_details
from admin_app.models import SystemSetting
from admin_app.services.backups import (
    build_database_backup_archive,
    get_database_backup_settings,
    restore_database_backup_file,
    save_database_backup_settings,
)
from admin_app.settings_registry import (
    invalidate_settings_cache,
    maintenance_mode_enabled,
    setting_key,
)
from auth_app.permissions import IsAdminRole


logger = logging.getLogger(__name__)


class DeletingFileResponse(FileResponse):
    def __init__(self, file_path, *args, **kwargs):
        self._delete_file_path = Path(file_path)
        super().__init__(self._delete_file_path.open("rb"), *args, **kwargs)

    def close(self):
        try:
            super().close()
        finally:
            self._delete_file_path.unlink(missing_ok=True)


def _maintenance_status():
    invalidate_settings_cache()
    return {"enabled": maintenance_mode_enabled()}


class AdminDatabaseBackupDownload(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        try:
            artifact = build_database_backup_archive(user=request.user)
        except Exception:
            logger.exception("Unable to create UMS backup archive.")
            return Response(
                {"message": "Unable to create the database backup. Check backend logs and try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = DeletingFileResponse(
            artifact.path,
            as_attachment=True,
            filename=artifact.filename,
            content_type="application/zip",
        )
        response["X-UMS-Backup-Created-At"] = artifact.created_at
        response["X-UMS-Maintenance-Changed"] = "false"
        return response


class AdminDatabaseBackupRestore(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        confirm_restore = str(request.data.get("confirm_restore", "")).strip().lower()
        if confirm_restore not in {"1", "true", "yes", "restore"}:
            return Response(
                {"message": "Confirm restore before replacing this server's data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload = request.FILES.get("backup_file")
        if upload is None:
            return Response(
                {"message": "Upload a UMS backup zip or generated SQL file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_name = str(upload.name or "").lower()
        if not (uploaded_name.endswith(".zip") or uploaded_name.endswith(".sql")):
            return Response(
                {"message": "Backup file must be a .zip archive or .sql file created by UMS."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        suffix = ".sql" if uploaded_name.endswith(".sql") else ".zip"
        temp_handle = tempfile.NamedTemporaryFile(prefix="ums-upload-", suffix=suffix, delete=False)
        temp_path = Path(temp_handle.name)
        try:
            for chunk in upload.chunks():
                temp_handle.write(chunk)
            temp_handle.close()

            result = restore_database_backup_file(temp_path, original_name=upload.name)
        except ValueError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unable to restore UMS backup archive.")
            return Response(
                {"message": "Unable to restore this backup. Maintenance mode remains on; check backend logs before retrying."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if not temp_handle.closed:
                temp_handle.close()
            temp_path.unlink(missing_ok=True)

        set_audit_details(
            request,
            {
                "backup_file": upload.name,
                "database_format": result.database_format,
                "media_files_restored": result.media_files_restored,
            },
        )
        return Response(
            {
                "message": "Backup restored successfully. Maintenance mode remains controlled manually.",
                "restored_at": result.restored_at,
                "manifest": result.manifest,
                "media_files_restored": result.media_files_restored,
                "database_format": result.database_format,
                "maintenance_mode": True,
                "maintenance_mode_changed": False,
            },
            status=status.HTTP_200_OK,
        )


class AdminDatabaseBackupSettings(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "settings": get_database_backup_settings(),
                "maintenance": _maintenance_status(),
            }
        )

    def patch(self, request):
        try:
            settings_payload = save_database_backup_settings(
                request.data,
                updated_by=request.user.profile,
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        set_audit_details(
            request,
            {
                "backup_settings": settings_payload,
                "high_impact": True,
            },
        )
        return Response(
            {
                "message": "Backup email settings updated successfully.",
                "settings": settings_payload,
                "maintenance": _maintenance_status(),
            }
        )


class AdminDatabaseBackupMaintenance(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request):
        if "maintenance_mode" not in request.data:
            return Response(
                {"maintenance_mode": "Provide true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        next_enabled = request.data.get("maintenance_mode")
        if not isinstance(next_enabled, bool):
            return Response(
                {"maintenance_mode": "Provide true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = str(request.data.get("reason") or "").strip()
        if not reason:
            return Response(
                {"reason": "A reason is required for maintenance mode changes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = SystemSetting.objects.filter(key=setting_key("security")).first()
        values = dict(record.value) if record and isinstance(record.value, dict) else {}
        previous = bool(values.get("maintenance_mode", False))
        values["maintenance_mode"] = next_enabled
        SystemSetting.objects.update_or_create(
            key=setting_key("security"),
            defaults={
                "value": values,
                "description": "High-impact access policies. Administrators retain access to settings and audit logs.",
                "updated_by": request.user.profile,
            },
        )
        invalidate_settings_cache()
        set_audit_details(
            request,
            {
                "changes": [
                    {
                        "setting": "security.maintenance_mode",
                        "previous_value": previous,
                        "new_value": next_enabled,
                    }
                ],
                "reason": reason,
                "high_impact": True,
            },
        )
        return Response(
            {
                "message": (
                    "Maintenance mode turned on."
                    if next_enabled
                    else "Maintenance mode turned off."
                ),
                "maintenance": _maintenance_status(),
            }
        )
