from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory

from admin_app.audit import AuditActionMiddleware
from admin_app.models import AuditLog, Profile


User = get_user_model()


def create_profile(username, role, first_name="", last_name=""):
    user = User.objects.create_user(
        username=username,
        password="pass",
        first_name=first_name,
        last_name=last_name,
        email=f"{username}@example.com",
    )
    profile = user.profile
    profile.role = role
    profile.save(update_fields=["role", "updated_at"])
    return user, profile


class AdminAuditLogTests(TestCase):
    def setUp(self):
        self.admin_user, self.admin_profile = create_profile(
            "admin_aisha",
            Profile.ROLE_ADMIN,
            "Aisha",
            "Rahman",
        )
        _, second_admin = create_profile("admin_omar", Profile.ROLE_ADMIN, "Omar", "Ali")
        _, executive = create_profile("exec_sara", Profile.ROLE_EXECUTIVE, "Sara", "Noor")
        AuditLog.objects.create(
            user=self.admin_profile,
            action="Updated system settings",
            object_type="System Settings",
            details={
                "changed_fields": ["timezone"],
                "setting": "timezone",
                "previous_value": "UTC",
                "new_value": "Asia/Kuala_Lumpur",
                "reason": "Use the university's local timezone.",
            },
        )
        AuditLog.objects.create(
            user=second_admin,
            action="Created user",
            object_type="Profile",
            object_id="17",
            details={"changed_fields": ["username", "role"]},
        )
        AuditLog.objects.create(
            user=executive,
            action="Updated organization",
            object_type="Organization",
            details={"scope": {"kind": "school", "id": 1}},
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)

    def test_admin_can_see_actor_account_for_all_audit_entries(self):
        response = self.client.get("/admin/audit-log")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        actors = {entry["actor"]["username"]: entry["actor"] for entry in response.data["results"]}
        self.assertEqual(actors["admin_aisha"]["full_name"], "Aisha Rahman")
        self.assertEqual(actors["admin_omar"]["role"], Profile.ROLE_ADMIN)
        self.assertEqual(actors["exec_sara"]["role"], Profile.ROLE_EXECUTIVE)

    def test_admin_can_filter_by_actor_action_and_object_type(self):
        response = self.client.get(
            "/admin/audit-log",
            {"actor": "omar", "action": "created", "object_type": "profile"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["actor"]["username"], "admin_omar")

    def test_admin_can_filter_and_search_settings_changes(self):
        filtered = self.client.get("/admin/audit-log", {"category": "settings"})
        searched = self.client.get("/admin/audit-log", {"search": "local timezone"})

        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["results"][0]["details"]["previous_value"], "UTC")
        self.assertEqual(searched.data["count"], 1)
        self.assertEqual(searched.data["results"][0]["object_type"], "System Settings")

    def test_middleware_records_structured_settings_change_details(self):
        request = APIRequestFactory().patch(
            "/admin/settings",
            {"timezone": "Asia/Kuala_Lumpur"},
            format="json",
        )
        request.user = self.admin_user

        def update_settings(incoming_request):
            incoming_request.audit_details = {
                "setting": "timezone",
                "previous_value": "UTC",
                "new_value": "Asia/Kuala_Lumpur",
                "reason": "Use the university's local timezone.",
                "high_impact": True,
                "secret_value": "must not be recorded",
            }
            return JsonResponse({"updated": True})

        AuditActionMiddleware(update_settings)(request)

        audit_entry = AuditLog.objects.latest("id")
        self.assertEqual(audit_entry.object_type, "Settings")
        self.assertEqual(audit_entry.details["previous_value"], "UTC")
        self.assertEqual(audit_entry.details["new_value"], "Asia/Kuala_Lumpur")
        self.assertEqual(audit_entry.details["reason"], "Use the university's local timezone.")
        self.assertTrue(audit_entry.details["high_impact"])
        self.assertNotIn("secret_value", audit_entry.details)
