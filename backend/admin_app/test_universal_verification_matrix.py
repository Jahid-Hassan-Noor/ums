import ast
import json
import re
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from admin_app.models import AcademicSession, Center, Profile, School, Semester, SystemSetting
from admin_app.settings_registry import (
    feature_flags,
    helpdesk_category_options,
    helpdesk_label,
    invalidate_settings_cache,
    public_settings_payload,
    setting_key,
)


User = get_user_model()

FORBIDDEN_RUNTIME_TERM_RE = re.compile(
    r"(?i:aiu|albukhary)|"
    r"\b(?:AIU|SBSS|SEHS|SCI|LC|CGS|CFGS|COR|CSAA|ICT|MYR|RM|Asia/Kuala_Lumpur)\b"
)


def assert_no_forbidden_terms(testcase, value):
    text = json.dumps(value, sort_keys=True, ensure_ascii=True)
    match = FORBIDDEN_RUNTIME_TERM_RE.search(text)
    if match:
        testcase.fail(f"Forbidden runtime term {match.group(0)!r} found in payload.")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="University Portal <portal@example.edu>",
    FRONTEND_BASE_URL="http://localhost:3000",
)
class UniversalVerificationProfileTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin_user = User.objects.create_superuser(
            username="matrix_admin",
            email="matrix-admin@example.edu",
            password="pass",
        )
        self.admin_profile = self.admin_user.profile
        self.admin_profile.role = Profile.ROLE_ADMIN
        self.admin_profile.save(update_fields=["role", "updated_at"])
        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)

    def tearDown(self):
        cache.clear()

    def configure(self, section, values):
        SystemSetting.objects.update_or_create(
            key=setting_key(section),
            defaults={"value": values, "updated_by": self.admin_profile},
        )
        invalidate_settings_cache()

    def test_neutral_profile_verifies_universal_runtime_contract(self):
        self.configure(
            "university",
            {
                "university_name": "Example Metropolitan University",
                "short_name": "EMU",
                "legal_name": "Example Metropolitan University",
                "tagline": "Learning across borders",
                "address": "100 Example Avenue",
                "phone": "+33 1 00 00 00 00",
                "email": "hello@example.edu",
                "admissions_email": "apply@example.edu",
                "website_url": "https://example.edu",
            },
        )
        self.configure(
            "localization",
            {
                "timezone": "Europe/Paris",
                "locale": "fr-FR",
                "currency_code": "EUR",
                "currency_symbol": "EUR",
            },
        )
        self.configure(
            "dashboard",
            {
                "enable_canteen": False,
                "enable_hostel": False,
                "enable_ict_helpdesk": True,
            },
        )
        self.configure(
            "workflow",
            {
                "default_application_number_prefix": "EMU",
                "payment_reference_prefix": "EMU-PAY",
            },
        )
        self.configure(
            "roles",
            {
                "module_ict_helpdesk_label": "Facilities Desk",
                "student_enabled_modules": "library,ict_helpdesk,notifications",
            },
        )
        self.configure(
            "helpdesk",
            {
                "helpdesk_display_label": "Facilities Desk",
                "helpdesk_reference_prefix": "FAC",
                "helpdesk_category_options": "maintenance|Maintenance\naccess|Access Cards",
                "helpdesk_status_labels": (
                    "submitted|Submitted\naddressed|Assigned\n"
                    "in_progress|In Progress\nsolved|Resolved"
                ),
            },
        )

        school = School.objects.create(code="BUS", name="Business School")
        semester_center = Center.objects.create(
            code="MET",
            name="Metropolitan Academic Center",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_SEMESTER,
        )
        annual_center = Center.objects.create(
            code="GLB",
            name="Global Studies Center",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_WHOLE_YEAR,
            annual_session_limit=4,
        )
        support_center = Center.objects.create(
            code="OPS",
            name="Operations Support Center",
            center_type=Center.CENTER_NON_ACADEMIC,
        )
        Semester.objects.create(
            name="EMU Term 1",
            academic_session="2026/2027",
            calendar_group=semester_center.effective_semester_calendar_group(),
            semester_number=1,
            is_active=True,
        )
        AcademicSession.objects.create(
            academic_session="2026",
            title="Global Studies Annual Session",
            center=annual_center,
            exam_date=date(2026, 12, 1),
        )

        public_response = self.client.get("/settings/public")
        admin_response = self.client.get("/admin/settings")
        account_response = self.client.post(
            "/admin/create-account/student",
            {
                "username": "emu_student",
                "email": "emu-student@example.edu",
                "first_name": "Neutral",
                "last_name": "Student",
                "ums_id": "EMU-1001",
                "school_id": school.id,
                "password": "Abcdefg1",
            },
            format="json",
        )

        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(account_response.status_code, 201, account_response.json())
        self.assertEqual(len(mail.outbox), 1)
        payload = public_settings_payload()
        assert_no_forbidden_terms(self, payload)
        self.assertEqual(payload["university"]["name"], "Example Metropolitan University")
        self.assertEqual(payload["localization"]["timezone"], "Europe/Paris")
        self.assertEqual(payload["localization"]["currency_code"], "EUR")
        self.assertEqual(payload["policies"]["default_application_number_prefix"], "EMU")
        self.assertFalse(feature_flags()["canteen"])
        self.assertFalse(feature_flags()["hostel"])
        self.assertEqual(payload["module_labels"]["ict_helpdesk"], "Facilities Desk")
        self.assertEqual(helpdesk_label(), "Facilities Desk")
        self.assertEqual(
            helpdesk_category_options(),
            [
                {"value": "maintenance", "label": "Maintenance"},
                {"value": "access", "label": "Access Cards"},
            ],
        )
        self.assertTrue(semester_center.uses_semester_calendar())
        self.assertEqual(semester_center.annual_session_limit, 0)
        self.assertFalse(annual_center.uses_semester_calendar())
        self.assertEqual(annual_center.annual_session_limit, 4)
        self.assertFalse(support_center.is_academic_center())

    def test_minimal_profile_has_neutral_empty_state(self):
        self.configure(
            "university",
            {
                "university_name": "Minimal Example University",
                "short_name": "MEU",
                "legal_name": "Minimal Example University",
                "email": "info@example.edu",
            },
        )
        self.configure(
            "dashboard",
            {
                "enable_public_website": False,
                "enable_admissions": False,
                "enable_canteen": False,
                "enable_library": False,
                "enable_ict_helpdesk": False,
                "enable_hostel": False,
                "enable_elections": False,
                "enable_finance": False,
            },
        )

        payload = public_settings_payload()

        assert_no_forbidden_terms(self, payload)
        self.assertEqual(payload["university"]["name"], "Minimal Example University")
        self.assertFalse(payload["features"]["public_website"])
        self.assertFalse(payload["features"]["admissions"])
        self.assertFalse(payload["features"]["canteen"])
        self.assertFalse(payload["features"]["ict_helpdesk"])
        self.assertEqual(School.objects.count(), 0)
        self.assertEqual(Center.objects.count(), 0)
        self.assertEqual(Semester.objects.count(), 0)


class UniversalRuntimeBrandingGuardTests(SimpleTestCase):
    SOURCE_SUFFIXES = {".py", ".ts", ".tsx"}
    SKIP_PARTS = {
        ".git",
        ".next",
        "__pycache__",
        "coverage",
        "dist",
        "build",
        "migrations",
        "node_modules",
    }
    TS_STRING_RE = re.compile(
        r"(?P<quote>['\"`])(?:\\.|(?!\1).)*(?P=quote)",
        re.DOTALL,
    )

    def project_root(self):
        return Path(__file__).resolve().parents[2]

    def is_allowed_path(self, relative_path):
        path = relative_path.as_posix()
        name = relative_path.name
        if "/tests/" in f"/{path}/" or name.startswith("test_") or name == "tests.py":
            return True
        if path.startswith("backend/admin_app/management/commands/") and "demo" in name:
            return True
        return False

    def runtime_source_files(self):
        root = self.project_root()
        for source_root in (root / "backend", root / "frontend"):
            for path in source_root.rglob("*"):
                if not path.is_file() or path.suffix not in self.SOURCE_SUFFIXES:
                    continue
                relative_path = path.relative_to(root)
                if any(part in self.SKIP_PARTS for part in relative_path.parts):
                    continue
                if self.is_allowed_path(relative_path):
                    continue
                yield path, relative_path

    def python_string_literals(self, path):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield node.lineno, node.value

    def typescript_string_literals(self, path):
        text = path.read_text(encoding="utf-8")
        for match in self.TS_STRING_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            yield line, match.group(0)

    def source_literals(self, path):
        if path.suffix == ".py":
            yield from self.python_string_literals(path)
        else:
            yield from self.typescript_string_literals(path)

    def test_runtime_source_literals_do_not_contain_aiu_specific_terms(self):
        violations = []
        for path, relative_path in self.runtime_source_files():
            for line, value in self.source_literals(path):
                match = FORBIDDEN_RUNTIME_TERM_RE.search(value)
                if match:
                    snippet = value.strip().replace("\n", "\\n")
                    violations.append(
                        f"{relative_path.as_posix()}:{line}: {match.group(0)!r} in {snippet[:120]!r}"
                    )

        if violations:
            self.fail(
                "AIU-specific runtime terms must stay in tests, docs, or explicit demo seed files.\n"
                + "\n".join(violations[:80])
            )
