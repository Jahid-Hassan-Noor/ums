import io
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from auth_app.auth_tokens import issue_ums_refresh
from admin_app.models import AuditLog, Building, Center, Profile, SystemSetting, Unit, Venue
from admin_app.role_config import resolve_role_ownership
from admin_app.settings_registry import (
    application_number_prefix,
    default_currency_code,
    features_enabled_for_path,
    format_currency_amount,
    institution_timezone,
    invalidate_settings_cache,
    password_policy_errors,
    public_settings_payload,
    role_module_enabled,
    setting_value,
    setup_completeness_payload,
)
from technician_app.venue_booking_service import validate_booking_payload


User = get_user_model()


class AdminSettingsTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.admin_user = User.objects.create_user(
            username="settings_admin",
            email="settings-admin@example.test",
            password="StrongPass123!",
        )
        self.admin_profile = self.admin_user.profile
        self.admin_profile.role = Profile.ROLE_ADMIN
        self.admin_profile.save(update_fields=["role", "updated_at"])
        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)
        cache.clear()

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()
        cache.clear()

    def image_upload(self, *, name="settings-logo.png", image_format="PNG"):
        image = Image.new("RGB", (20, 20), color="teal")
        content = io.BytesIO()
        image.save(content, format=image_format)
        content.seek(0)
        return SimpleUploadedFile(
            name,
            content.read(),
            content_type=f"image/{image_format.lower()}",
        )

    def enable_maintenance_mode(self):
        SystemSetting.objects.update_or_create(
            key="ums.security",
            defaults={
                "value": {"maintenance_mode": True},
                "updated_by": self.admin_profile,
            },
        )
        invalidate_settings_cache()

    def test_admin_can_load_all_settings_sections(self):
        response = self.client.get("/admin/settings")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [section["key"] for section in response.data["sections"]],
            [
                "general",
                "university",
                "localization",
                "terminology",
                "academic",
                "workflow",
                "notifications",
                "dashboard",
                "helpdesk",
                "venue_booking_policy",
                "hostel_policy",
                "roles",
                "security",
                "canteen_policy",
                "librarian_library",
            ],
        )
        self.assertEqual(
            response.data["sections"][2]["values"]["timezone"],
            "UTC",
        )
        self.assertFalse(response.data["setup_checklist"]["complete"])
        notification_section = next(
            section
            for section in response.data["sections"]
            if section["key"] == "notifications"
        )
        notification_fields = {
            field["key"] for field in notification_section["fields"]
        }
        self.assertIn("notify_sec_set_reminders", notification_fields)
        self.assertIn("notify_library_due_reminders", notification_fields)
        image_fields = {
            (section["key"], field["key"]): field["type"]
            for section in response.data["sections"]
            for field in section["fields"]
            if field["type"] == "image"
        }
        self.assertEqual(image_fields[("university", "logo_url")], "image")
        self.assertEqual(image_fields[("university", "public_hero_image_url")], "image")
        self.assertEqual(image_fields[("university", "social_image_url")], "image")
        ui_response = self.client.get("/admin/ui-customization")
        self.assertEqual(ui_response.status_code, 200)
        ui_image_fields = {
            field["key"]: field["type"]
            for field in ui_response.data["section"]["fields"]
            if field["type"] == "image"
        }
        self.assertEqual(ui_image_fields["logo_url"], "image")
        self.assertEqual(ui_image_fields["default_avatar_url"], "image")
        self.assertEqual(ui_image_fields["dashboard_background_image_url"], "image")

    def test_maintenance_mode_blocks_public_pages_but_public_settings_stay_readable(self):
        self.enable_maintenance_mode()
        public_client = APIClient()

        settings_response = public_client.get("/settings/public")
        home_response = public_client.get("/")

        self.assertEqual(settings_response.status_code, 200)
        self.assertTrue(settings_response.json()["maintenance"]["enabled"])
        self.assertEqual(home_response.status_code, 503)
        self.assertEqual(
            home_response.json()["detail"],
            "The UMS is currently in maintenance mode.",
        )

    def test_maintenance_mode_allows_django_admin_login_page(self):
        self.enable_maintenance_mode()
        public_client = APIClient()

        response = public_client.get("/super_admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/super_admin/login/", response["Location"])

    def test_login_accepts_unique_email_identifier(self):
        auth_client = APIClient()

        response = auth_client.post(
            "/auth/login",
            {"username": self.admin_user.email, "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], self.admin_user.username)

    def test_login_does_not_guess_when_email_matches_multiple_accounts(self):
        second_admin = User.objects.create_user(
            username="settings_admin_two",
            email=self.admin_user.email,
            password="StrongPass123!",
        )
        second_admin.profile.role = Profile.ROLE_ADMIN
        second_admin.profile.save(update_fields=["role", "updated_at"])
        auth_client = APIClient()

        response = auth_client.post(
            "/auth/login",
            {"username": self.admin_user.email, "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_maintenance_mode_allows_admin_login_and_blocks_non_admin_sessions(self):
        self.enable_maintenance_mode()
        student = User.objects.create_user(
            username="maintenance_student",
            password="StrongPass123!",
        )
        student.profile.role = Profile.ROLE_STUDENT
        student.profile.save(update_fields=["role", "updated_at"])
        auth_client = APIClient()

        student_login = auth_client.post(
            "/auth/login",
            {"username": student.username, "password": "StrongPass123!"},
            format="json",
        )
        admin_login = auth_client.post(
            "/auth/login",
            {"username": self.admin_user.username, "password": "StrongPass123!"},
            format="json",
        )
        admin_email_login = auth_client.post(
            "/auth/login",
            {"username": self.admin_user.email, "password": "StrongPass123!"},
            format="json",
        )
        applicant_login = auth_client.post(
            "/applicant/auth/login",
            {"username": "anyone", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(student_login.status_code, 503)
        self.assertEqual(applicant_login.status_code, 503)
        self.assertEqual(admin_login.status_code, 200)
        self.assertEqual(admin_email_login.status_code, 200)

        self.client.force_authenticate(student)
        me_response = self.client.get("/auth/me")
        self.assertEqual(me_response.status_code, 503)

        refresh_response = auth_client.post(
            "/auth/token/refresh",
            {"refresh": str(issue_ums_refresh(student))},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 503)

    def test_high_impact_change_requires_reason_and_is_audited(self):
        without_reason = self.client.patch(
            "/admin/settings",
            {
                "section": "security",
                "values": {"read_only_mode": True},
                "reason": "",
            },
            format="json",
        )
        self.assertEqual(without_reason.status_code, 400)
        self.assertFalse(SystemSetting.objects.filter(key="ums.security").exists())

        updated = self.client.patch(
            "/admin/settings",
            {
                "section": "security",
                "values": {"read_only_mode": True},
                "reason": "Protect data during the scheduled upgrade.",
            },
            format="json",
        )

        self.assertEqual(updated.status_code, 200)
        self.assertTrue(setting_value("security", "read_only_mode"))
        audit = AuditLog.objects.latest("id")
        self.assertTrue(audit.details["high_impact"])
        self.assertEqual(
            audit.details["reason"],
            "Protect data during the scheduled upgrade.",
        )
        self.assertEqual(audit.details["changes"][0]["setting"], "security.read_only_mode")
        blocked = self.client.post("/admin/canteen", {}, format="json")
        self.assertEqual(blocked.status_code, 503)

    def test_dashboard_settings_publish_public_profile_and_feature_flags(self):
        updated = self.client.patch(
            "/admin/settings",
            {
                "section": "dashboard",
                "values": {
                    "enable_venue_booking": False,
                    "enable_elections": False,
                },
                "reason": "Disable venue booking and elections for this institution.",
            },
            format="json",
        )

        self.assertEqual(updated.status_code, 200)
        self.assertFalse(features_enabled_for_path("/student/venue-bookings"))
        self.assertFalse(features_enabled_for_path("/admin/venue-bookings"))
        self.assertFalse(features_enabled_for_path("/student/elections"))
        self.assertFalse(features_enabled_for_path("/technician/elections"))
        self.assertFalse(features_enabled_for_path("/ict-helpdesk/technician/elections"))
        self.assertTrue(features_enabled_for_path("/student/library/books"))
        self.assertTrue(features_enabled_for_path("/student/subscriptions"))
        payload = public_settings_payload()
        self.assertFalse(payload["features"]["venue_booking"])
        self.assertFalse(payload["features"]["elections"])
        self.assertTrue(payload["features"]["admissions"])
        self.assertTrue(payload["features"]["finance"])
        self.assertNotIn("gym_subscription", payload["features"])
        self.assertNotIn("kitchen_subscription", payload["features"])

    def test_role_settings_publish_labels_and_module_permissions(self):
        response = self.client.patch(
            "/admin/settings",
            {
                "section": "roles",
                "values": {
                    "student_label": "Learner",
                    "module_ict_helpdesk_label": "Service Desk",
                    "student_enabled_modules": "library,notifications",
                },
                "reason": "Configure role labels and student module ownership.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.json())
        payload = public_settings_payload()
        self.assertEqual(payload["roles"]["student"]["label"], "Learner")
        self.assertEqual(payload["module_labels"]["ict_helpdesk"], "Service Desk")
        self.assertEqual(
            payload["module_permissions"]["student"],
            ["library", "notifications"],
        )
        self.assertTrue(features_enabled_for_path("/student/elections"))
        self.assertFalse(features_enabled_for_path("/student/elections", role="student"))
        self.assertTrue(role_module_enabled("student", "library"))
        self.assertFalse(role_module_enabled("student", "elections"))

    def test_role_owner_settings_resolve_special_role_defaults(self):
        center = Center.objects.create(code="LIB", name="Library Services")
        unit = Unit.objects.create(code="LIB-OPS", name="Library Operations", center=center)
        response = self.client.patch(
            "/admin/settings",
            {
                "section": "roles",
                "values": {
                    "librarian_default_center_code": center.code,
                    "librarian_default_unit_code": unit.code,
                },
                "reason": "Move library ownership to configured organization records.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.json())
        ownership = resolve_role_ownership(Profile.ROLE_LIBRARIAN)

        self.assertEqual(ownership["center"], center)
        self.assertEqual(ownership["unit"], unit)
        self.assertIsNone(ownership["school"])
        self.assertIsNone(ownership["department"])

    def test_public_settings_expose_universal_institution_contract(self):
        response = self.client.patch(
            "/admin/settings",
            {
                "section": "localization",
                "values": {
                    "timezone": "America/New_York",
                    "locale": "en-US",
                    "currency_code": "USD",
                    "currency_symbol": "$",
                },
                "reason": "Configure a non-demo institution locale.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = public_settings_payload()
        self.assertEqual(payload["localization"]["timezone"], "America/New_York")
        self.assertEqual(payload["localization"]["currency_code"], "USD")
        self.assertEqual(payload["terminology"]["center_label"], "Center")
        self.assertEqual(payload["terminology"]["centre_label"], "Center")
        self.assertEqual(payload["terminology"]["programme_label"], "Program")
        self.assertEqual(payload["policies"]["default_application_number_prefix"], "APP")
        self.assertEqual(payload["policies"]["default_payment_gateway_provider"], "manual")
        self.assertTrue(payload["policies"]["dining"]["enabled"])
        self.assertTrue(payload["policies"]["venue_booking"]["enabled"])
        self.assertEqual(payload["policies"]["venue_booking"]["reviewer_role"], "technician")
        self.assertEqual(
            payload["policies"]["venue_booking"]["venue_categories"][0],
            {"value": "classroom", "label": "Classroom"},
        )
        self.assertEqual(payload["policies"]["dining"]["label"], "Dining")
        self.assertEqual(payload["policies"]["dining"]["monthly_allowance_amount"], "50.00")
        self.assertEqual(payload["policies"]["dining"]["allowance_reset_hour"], 8)
        self.assertFalse(payload["setup"]["complete"])
        self.assertEqual(str(institution_timezone()), "America/New_York")
        self.assertEqual(default_currency_code(), "USD")
        self.assertEqual(format_currency_amount("12.5"), "$12.50")

    def test_setup_checklist_completes_after_required_identity_updates(self):
        identity_response = self.client.patch(
            "/admin/settings",
            {
                "section": "university",
                "values": {
                    "university_name": "Example State University",
                    "short_name": "ESU",
                    "legal_name": "Example State University LLC",
                    "tagline": "Learning for every community",
                    "address": "100 College Avenue",
                    "phone": "+1 555 0100",
                    "email": "hello@esu.example",
                    "admissions_email": "apply@esu.example",
                },
                "reason": "Complete required institution identity.",
            },
            format="json",
        )
        workflow_response = self.client.patch(
            "/admin/settings",
            {
                "section": "workflow",
                "values": {"default_application_number_prefix": "ESU"},
                "reason": "Use the institution application prefix.",
            },
            format="json",
        )

        self.assertEqual(identity_response.status_code, 200)
        self.assertEqual(workflow_response.status_code, 200)
        checklist = setup_completeness_payload()
        self.assertTrue(checklist["complete"])
        self.assertTrue(workflow_response.data["setup_checklist"]["complete"])
        self.assertEqual(application_number_prefix(), "ESU")

    def test_admin_setup_wizard_reports_programmatic_steps(self):
        response = self.client.get("/admin/setup-wizard")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Universal Setup Wizard")
        step_keys = [step["key"] for step in response.data["steps"]]
        self.assertEqual(
            step_keys,
            [
                "institution_profile",
                "branding",
                "localization",
                "terminology",
                "academic_structure",
                "academic_calendars",
                "enabled_modules",
                "role_ownership",
                "admissions",
                "public_website",
            ],
        )
        self.assertFalse(response.data["summary"]["complete"])
        self.assertGreater(response.data["summary"]["missing_required_items"], 0)
        self.assertTrue(
            any(
                message["step"] == "institution_profile"
                for message in response.data["messages"]
            )
        )
        academic_step = next(
            step
            for step in response.data["steps"]
            if step["key"] == "academic_structure"
        )
        self.assertTrue(
            any(
                item["key"] == "academic_structure.school_or_center"
                for item in academic_step["items"]
            )
        )

    def test_disabled_modules_do_not_block_setup_wizard_messages(self):
        SystemSetting.objects.update_or_create(
            key="ums.dashboard",
            defaults={
                "value": {
                    "enable_admissions": False,
                    "enable_public_website": False,
                    "enable_canteen": False,
                    "enable_library": False,
                    "enable_ict_helpdesk": False,
                    "enable_finance": False,
                },
                "updated_by": self.admin_profile,
            },
        )
        invalidate_settings_cache()

        response = self.client.get("/admin/setup-wizard")

        self.assertEqual(response.status_code, 200)
        message_steps = {message["step"] for message in response.data["messages"]}
        self.assertNotIn("admissions", message_steps)
        self.assertNotIn("public_website", message_steps)
        role_step = next(
            step
            for step in response.data["steps"]
            if step["key"] == "role_ownership"
        )
        owner_items = {item["key"]: item for item in role_step["items"]}
        self.assertTrue(owner_items["role_ownership.library"]["complete"])
        self.assertFalse(owner_items["role_ownership.library"]["required"])
        self.assertTrue(owner_items["role_ownership.canteen"]["complete"])
        self.assertTrue(owner_items["role_ownership.ict_helpdesk"]["complete"])
        self.assertTrue(owner_items["role_ownership.finance"]["complete"])

    def test_localization_validation_rejects_invalid_values(self):
        timezone_response = self.client.patch(
            "/admin/settings",
            {
                "section": "localization",
                "values": {"timezone": "Mars/Olympus"},
                "reason": "Testing validation.",
            },
            format="json",
        )
        currency_response = self.client.patch(
            "/admin/settings",
            {
                "section": "localization",
                "values": {"currency_code": "US"},
                "reason": "Testing validation.",
            },
            format="json",
        )

        self.assertEqual(timezone_response.status_code, 400)
        self.assertIn("timezone", timezone_response.data)
        self.assertEqual(currency_response.status_code, 400)
        self.assertIn("currency_code", currency_response.data)

    def test_canteen_policy_validation_rejects_invalid_values(self):
        amount_response = self.client.patch(
            "/admin/settings",
            {
                "section": "canteen_policy",
                "values": {"monthly_allowance_amount": "-1"},
                "reason": "Testing validation.",
            },
            format="json",
        )
        timezone_response = self.client.patch(
            "/admin/settings",
            {
                "section": "canteen_policy",
                "values": {"allowance_reset_timezone": "Mars/Olympus"},
                "reason": "Testing validation.",
            },
            format="json",
        )

        self.assertEqual(amount_response.status_code, 400)
        self.assertIn("monthly_allowance_amount", amount_response.data)
        self.assertEqual(timezone_response.status_code, 400)
        self.assertIn("allowance_reset_timezone", timezone_response.data)

    def test_venue_booking_policy_validation_rejects_invalid_values(self):
        roles_response = self.client.patch(
            "/admin/settings",
            {
                "section": "venue_booking_policy",
                "values": {"requester_roles": "student,alumni"},
                "reason": "Testing validation.",
            },
            format="json",
        )
        blackout_response = self.client.patch(
            "/admin/settings",
            {
                "section": "venue_booking_policy",
                "values": {"blackout_dates": "2026-13-01"},
                "reason": "Testing validation.",
            },
            format="json",
        )
        duration_response = self.client.patch(
            "/admin/settings",
            {
                "section": "venue_booking_policy",
                "values": {
                    "min_duration_minutes": 180,
                    "max_duration_hours": 2,
                },
                "reason": "Testing validation.",
            },
            format="json",
        )

        self.assertEqual(roles_response.status_code, 400)
        self.assertIn("requester_roles", roles_response.data)
        self.assertEqual(blackout_response.status_code, 400)
        self.assertIn("blackout_dates", blackout_response.data)
        self.assertEqual(duration_response.status_code, 400)
        self.assertIn("max_duration_hours", duration_response.data)

    def test_section_validation_rejects_invalid_credit_range(self):
        response = self.client.patch(
            "/admin/settings",
            {
                "section": "academic",
                "values": {
                    "registration_min_credit_hours": 22,
                    "registration_max_credit_hours": 21,
                },
                "reason": "Testing invalid policy.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("registration_max_credit_hours", response.data)

    def test_workflow_setting_controls_venue_booking_notice(self):
        SystemSetting.objects.create(
            key="portal.workflow",
            value={"venue_booking_min_notice_days": 3},
            updated_by=self.admin_profile,
        )
        invalidate_settings_cache()
        building = Building.objects.create(code="BLD", name="Building")
        venue = Venue.objects.create(
            building=building,
            code="ROOM",
            name="Room",
            capacity=10,
        )

        payload, error = validate_booking_payload(
            {
                "venue_id": venue.id,
                "booking_type": "event",
                "purpose": "Workshop",
                "explanation": "A detailed workshop explanation.",
                "booking_date": (timezone.localdate() + timedelta(days=2)).isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
            }
        )

        self.assertIsNone(payload)
        self.assertIn("at least 3 day(s) notice", error)

    def test_admin_can_create_test_notification(self):
        response = self.client.post(
            "/admin/settings",
            {"action": "test_notification"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.admin_profile.notifications.filter(data__settings_test=True).exists())

    def test_admin_can_upload_settings_image_and_publish_database_url(self):
        response = self.client.post(
            "/admin/settings",
            {
                "action": "upload_image",
                "section": "university",
                "field": "logo_url",
                "file": self.image_upload(),
                "reason": "Refresh uploaded branding.",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        image_url = response.data["url"]
        self.assertTrue(image_url.startswith("/media/settings/images/university/logo_url/"))
        self.assertEqual(setting_value("university", "logo_url"), image_url)
        self.assertEqual(public_settings_payload()["university"]["logo_url"], image_url)
        audit = AuditLog.objects.latest("id")
        self.assertEqual(audit.details["changes"][0]["setting"], "university.logo_url")
        self.assertEqual(audit.details["changes"][0]["new_value"], image_url)

    def test_ui_customization_loader_settings_publish_public_payload(self):
        response = self.client.patch(
            "/admin/ui-customization",
            {
                "values": {
                    "loading_spinner": "vortex",
                    "loading_spinner_size": 120,
                },
                "reason": "Use a branded loading animation.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.data["public_payload"]["ui_customization"]
        self.assertEqual(payload["loading_spinner"], "vortex")
        self.assertEqual(payload["loading_spinner_size"], 120)
        current_payload = public_settings_payload()["ui_customization"]
        self.assertEqual(current_payload["loading_spinner"], "vortex")
        self.assertEqual(current_payload["loading_spinner_size"], 120)

    def test_settings_image_upload_rejects_non_image_fields(self):
        response = self.client.post(
            "/admin/settings",
            {
                "action": "upload_image",
                "section": "university",
                "field": "university_name",
                "file": self.image_upload(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("field", response.data)

    def test_password_policy_is_available_to_account_workflows(self):
        SystemSetting.objects.create(
            key="portal.security",
            value={
                "password_min_length": 12,
                "password_max_length": 20,
                "password_require_uppercase": True,
                "password_require_number": True,
            },
            updated_by=self.admin_profile,
        )
        invalidate_settings_cache()

        self.assertEqual(len(password_policy_errors("short")), 3)
        self.assertEqual(password_policy_errors("StrongPassword123"), [])
        self.assertEqual(
            password_policy_errors("StrongPassword1234567890"),
            ["Password must contain 20 characters or fewer."],
        )
