from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admin_app.models import AuditLog, Profile, School


User = get_user_model()


def create_executive(username, school):
    user = User.objects.create_user(username=username, password="pass")
    profile = user.profile
    profile.role = Profile.ROLE_EXECUTIVE
    profile.school = school
    profile.save(update_fields=["role", "school", "updated_at"])
    return user, profile


class ExecutiveAuditLogTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        other_school = School.objects.create(code="SBM", name="School of Business")
        self.user, self.profile = create_executive("exec_aisha", self.school)
        _, colleague = create_executive("exec_omar", self.school)
        _, outsider = create_executive("exec_sara", other_school)

        AuditLog.objects.create(
            user=colleague,
            action="Updated organization",
            object_type="Organization",
            details={"scope": {"kind": "school", "id": self.school.id}},
        )
        AuditLog.objects.create(
            user=outsider,
            action="Updated organization",
            object_type="Organization",
            details={"scope": {"kind": "school", "id": other_school.id}},
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_executive_sees_only_executive_actions_in_the_same_scope(self):
        response = self.client.get("/executive/audit-log")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope"]["id"], self.school.id)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["actor"]["username"], "exec_omar")

    def test_successful_executive_change_is_logged_with_actor_and_scope(self):
        response = self.client.patch(
            "/executive/organization",
            {"description": "Updated by the school executive."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        log = AuditLog.objects.get(user=self.profile)
        self.assertEqual(log.action, "Updated organization")
        self.assertEqual(log.details["changed_fields"], ["description"])
        self.assertEqual(log.details["scope"]["kind"], "school")
        self.assertEqual(log.details["scope"]["id"], self.school.id)
        self.assertEqual(log.object_id, str(self.school.id))
