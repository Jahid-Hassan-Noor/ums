import io
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from admin_app.models import SystemSetting
from admin_app.services.backups import (
    BACKUP_JSON_FILENAME,
    BACKUP_MANIFEST_FILENAME,
    BACKUP_MEDIA_PREFIX,
    BACKUP_SQL_FILENAME,
    SQL_BACKUP_MARKER,
    BackupArtifact,
    build_database_backup_archive,
    send_monthly_backup_email,
    validate_backup_archive,
)
from admin_app.settings_registry import invalidate_settings_cache, setting_key
from admin_app.settings_registry import maintenance_mode_enabled
from auth_app.models import Profile


User = get_user_model()


def backup_upload(name, content, content_type="application/zip"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def archive_bytes(entries):
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name, value)
    content.seek(0)
    return content.read()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AdminDatabaseBackupTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.admin_user = User.objects.create_user(
            username="backup_admin",
            email="backup-admin@example.test",
            password="StrongPass123!",
        )
        self.admin_profile = self.admin_user.profile
        self.admin_profile.role = Profile.ROLE_ADMIN
        self.admin_profile.save(update_fields=["role", "updated_at"])
        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)
        invalidate_settings_cache()

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()
        invalidate_settings_cache()

    def enable_maintenance_mode(self):
        SystemSetting.objects.update_or_create(
            key=setting_key("security"),
            defaults={
                "value": {"maintenance_mode": True},
                "updated_by": self.admin_profile,
            },
        )
        invalidate_settings_cache()

    def test_non_admin_cannot_download_backup(self):
        student = User.objects.create_user(
            username="backup_student",
            password="StrongPass123!",
        )
        student.profile.role = Profile.ROLE_STUDENT
        student.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(student)

        response = self.client.post("/admin/database-backup")

        self.assertEqual(response.status_code, 403)

    def test_backup_zip_contains_database_manifest_sql_and_media_without_maintenance_toggle(self):
        media_file = Path(self.media_dir.name) / "profiles" / "sample.txt"
        media_file.parent.mkdir(parents=True)
        media_file.write_text("sample media", encoding="utf-8")

        def write_sql(path):
            Path(path).write_text(f"{SQL_BACKUP_MARKER}\nselect 1;\n", encoding="utf-8")

        with patch("admin_app.services.backups._write_database_sql_dump", side_effect=write_sql):
            artifact = build_database_backup_archive(user=self.admin_user)

        try:
            self.assertFalse(maintenance_mode_enabled())
            with zipfile.ZipFile(artifact.path) as archive:
                names = set(archive.namelist())
                self.assertIn(BACKUP_JSON_FILENAME, names)
                self.assertIn(BACKUP_SQL_FILENAME, names)
                self.assertIn(BACKUP_MANIFEST_FILENAME, names)
                self.assertIn(f"{BACKUP_MEDIA_PREFIX}/profiles/sample.txt", names)
                manifest = json.loads(archive.read(BACKUP_MANIFEST_FILENAME).decode("utf-8"))
                self.assertEqual(manifest["app"], "UMS")
                self.assertEqual(manifest["database_formats"], ["sql", "json"])
                self.assertFalse(manifest["maintenance_mode_changed"])
        finally:
            artifact.path.unlink(missing_ok=True)

    def test_backup_zip_falls_back_to_json_when_postgres_tools_are_missing(self):
        with patch(
            "admin_app.services.backups._write_database_sql_dump",
            side_effect=RuntimeError("PostgreSQL client tools are not installed in the backend container."),
        ):
            artifact = build_database_backup_archive(user=self.admin_user)

        try:
            with zipfile.ZipFile(artifact.path) as archive:
                names = set(archive.namelist())
                self.assertIn(BACKUP_JSON_FILENAME, names)
                self.assertNotIn(BACKUP_SQL_FILENAME, names)
                manifest = json.loads(archive.read(BACKUP_MANIFEST_FILENAME).decode("utf-8"))
                self.assertEqual(manifest["database_formats"], ["json"])
                self.assertIn("sql_backup_warning", manifest)
        finally:
            artifact.path.unlink(missing_ok=True)

    def test_restore_requires_manual_maintenance_mode(self):
        payload = archive_bytes({BACKUP_JSON_FILENAME: "[]"})

        response = self.client.post(
            "/admin/database-backup/restore",
            {
                "backup_file": backup_upload("ums-backup.zip", payload),
                "confirm_restore": "true",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("maintenance mode", response.data["message"].lower())

    def test_restore_rejects_unmarked_sql_backup(self):
        self.enable_maintenance_mode()

        response = self.client.post(
            "/admin/database-backup/restore",
            {
                "backup_file": backup_upload(
                    "foreign.sql",
                    b"drop table anything;",
                    content_type="application/sql",
                ),
                "confirm_restore": "true",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("generated by the UMS backup tool", response.data["message"])

    def test_restore_rejects_media_path_traversal(self):
        payload = archive_bytes(
            {
                BACKUP_JSON_FILENAME: "[]",
                f"{BACKUP_MEDIA_PREFIX}/../evil.txt": "bad",
            }
        )
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
            archive_path = Path(handle.name)
            handle.write(payload)

        try:
            with self.assertRaisesMessage(ValueError, "Unsafe media path"):
                validate_backup_archive(archive_path)
        finally:
            archive_path.unlink(missing_ok=True)

    def test_restore_reports_json_format_and_preserves_maintenance_mode(self):
        self.enable_maintenance_mode()
        payload = archive_bytes(
            {
                BACKUP_JSON_FILENAME: "[]",
                BACKUP_MANIFEST_FILENAME: json.dumps({"created_at": "2026-07-15T00:00:00+00:00"}),
            }
        )

        with patch("admin_app.services.backups.call_command") as call_command:
            response = self.client.post(
                "/admin/database-backup/restore",
                {
                    "backup_file": backup_upload("ums-backup.zip", payload),
                    "confirm_restore": "restore",
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["database_format"], "json")
        self.assertTrue(response.data["maintenance_mode"])
        self.assertTrue(
            SystemSetting.objects.get(key=setting_key("security")).value["maintenance_mode"]
        )
        self.assertGreaterEqual(call_command.call_count, 2)

    def test_backup_email_settings_can_be_updated_and_validated(self):
        response = self.client.patch(
            "/admin/database-backup/settings",
            {
                "monthly_email_enabled": True,
                "recipients": [
                    "backup@example.edu",
                    "backup@example.edu",
                    "audit@example.edu",
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["settings"]["recipients"],
            ["backup@example.edu", "audit@example.edu"],
        )
        self.assertTrue(response.data["settings"]["monthly_email_enabled"])

        invalid = self.client.patch(
            "/admin/database-backup/settings",
            {"recipients": ["not-an-email"]},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)

    def test_monthly_backup_email_sends_when_enabled(self):
        SystemSetting.objects.update_or_create(
            key="ums.backup_restore",
            defaults={
                "value": {
                    "monthly_email_enabled": True,
                    "recipients": ["backup@example.edu"],
                },
                "updated_by": self.admin_profile,
            },
        )
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
            artifact_path = Path(handle.name)
            handle.write(b"zip-bytes")

        artifact = BackupArtifact(
            path=artifact_path,
            filename="ums-backup-test.zip",
            created_at="2026-07-15T00:00:00+00:00",
        )
        with patch("admin_app.services.backups.build_database_backup_archive", return_value=artifact):
            result = send_monthly_backup_email()

        self.assertTrue(result["sent"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["backup@example.edu"])
        self.assertEqual(mail.outbox[0].attachments[0][0], "ums-backup-test.zip")
        self.assertFalse(artifact_path.exists())
