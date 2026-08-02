import io
import tempfile
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from admin_app.models import AuditLog, Profile, ReportExport
from applicant_app.models import Applicant


User = get_user_model()


class AdminReportTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.admin = User.objects.create_superuser(
            username="reports_admin",
            email="reports@example.com",
            password="pass",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    def _applicant(self, username, nationality):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            first_name=username.title(),
            password="pass",
        )
        profile = user.profile
        profile.role = Profile.ROLE_APPLICANT
        profile.save(update_fields=["role", "updated_at"])
        applicant, _created = Applicant.objects.update_or_create(
            profile=profile,
            defaults={
                "nationality": nationality,
                "country_of_residence": nationality,
            },
        )
        return applicant

    def test_catalog_report_is_stored_and_can_be_downloaded(self):
        response = self.client.get("/admin/reports/generate/academic-directory")

        self.assertEqual(response.status_code, 200)
        report = ReportExport.objects.get(export_type="academic-directory")
        self.assertEqual(report.status, ReportExport.STATUS_COMPLETED)
        self.assertTrue(report.file)
        self.assertTrue(
            AuditLog.objects.filter(
                action="report.export.completed",
                object_id=str(report.id),
            ).exists()
        )
        self.assertTrue(
            self.admin.profile.notifications.filter(
                data__event_type="reports.completed",
                data__report_export_id=report.id,
            ).exists()
        )

        history = self.client.get("/admin/reports/exports")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["summary"]["completed"], 1)

        download = self.client.get(f"/admin/reports/exports/{report.id}")
        self.assertEqual(download.status_code, 200)
        self.assertTrue(b"".join(download.streaming_content).startswith(b"PK"))

    def test_applicant_export_applies_report_filters(self):
        self._applicant("malaysia_applicant", "Malaysia")
        self._applicant("indonesia_applicant", "Indonesia")

        response = self.client.get(
            "/admin/manage/applicants/export",
            {"nationality": "Malaysia"},
        )

        self.assertEqual(response.status_code, 200)
        with ZipFile(io.BytesIO(response.content)) as workbook:
            sheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("malaysia_applicant", sheet)
        self.assertNotIn("indonesia_applicant", sheet)

        report = ReportExport.objects.get(export_type="applicants")
        self.assertEqual(report.filters["nationality"], "Malaysia")
        self.assertEqual(report.filters["row_count"], 1)

    def test_report_history_file_can_be_removed(self):
        self.client.get("/admin/reports/generate/audit-log")
        report = ReportExport.objects.get(export_type="audit-log")

        response = self.client.delete(f"/admin/reports/exports/{report.id}")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ReportExport.objects.filter(pk=report.id).exists())
        self.assertTrue(
            AuditLog.objects.filter(
                action="report.export.deleted",
                object_id=str(report.id),
            ).exists()
        )
