from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Department, Profile, SystemSetting
from admin_app.settings_registry import invalidate_settings_cache, setting_key
from auth_app.serializers import RegisterSerializer
from notifications_package.models import Notification
from technician_app.models import Election, HelpdeskTicket, Technician


User = get_user_model()


class ServiceDeskWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department, _created = Department.objects.update_or_create(
            code="SUPPORT",
            defaults={"name": "Service Desk Department", "school": None, "center": None},
        )
        SystemSetting.objects.update_or_create(
            key=setting_key("roles"),
            defaults={
                "value": {
                    "technician_default_department_code": self.department.code,
                }
            },
        )
        invalidate_settings_cache()

        self.technician_user = User.objects.create_user(username="technician", password="pass")
        self.technician = self.technician_user.profile
        self.technician.role = Profile.ROLE_TECHNICIAN
        self.technician.department = self.department
        self.technician.save()
        Technician.objects.update_or_create(
            profile=self.technician,
            defaults={
                "technician_id": "SUP-001",
                "department": self.department,
                "is_active": True,
            },
        )

        self.student_user = User.objects.create_user(username="student_helpdesk", password="pass")
        self.student = self.student_user.profile
        self.student.student_id = "STD-SUP-1"
        self.student.save(update_fields=["student_id", "updated_at"])

    def _configure_helpdesk(self, values):
        SystemSetting.objects.update_or_create(
            key=setting_key("helpdesk"),
            defaults={"value": values},
        )
        invalidate_settings_cache()

    def test_technician_account_is_created_under_configured_department(self):
        serializer = RegisterSerializer(
            data={
                "username": "new_technician",
                "email": "new-technician@example.com",
                "first_name": "New",
                "last_name": "Technician",
                "password": "StrongPass123!",
                "role": Profile.ROLE_TECHNICIAN,
                "ums_id": "SUP-100",
                "department_id": self.department.id,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.department, self.department)
        self.assertIsNone(user.profile.center)
        self.assertIsNone(user.profile.school)
        self.assertIsNone(user.profile.unit)
        self.assertTrue(Technician.objects.filter(profile=user.profile, technician_id="SUP-100").exists())

    def test_student_submits_ticket_and_technician_updates_progress(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(
            "/ict-helpdesk/student/tickets",
            {
                "category": "wifi",
                "subject": "Cannot connect in hostel",
                "description": "The university Wi-Fi rejects my account.",
                "location": "Hostel A",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        ticket = HelpdeskTicket.objects.get()
        self.assertEqual(ticket.status, HelpdeskTicket.STATUS_SUBMITTED)
        self.assertTrue(Notification.objects.filter(recipient=self.technician, data__ticket_id=ticket.id).exists())

        self.client.force_authenticate(user=self.technician_user)
        response = self.client.patch(
            f"/ict-helpdesk/technician/tickets/{ticket.id}",
            {"status": "in_progress", "note": "Checking the hotspot account."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, HelpdeskTicket.STATUS_IN_PROGRESS)
        self.assertEqual(ticket.assigned_to, self.technician)
        self.assertTrue(Notification.objects.filter(recipient=self.student, data__ticket_id=ticket.id).exists())

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/ict-helpdesk/student/tickets")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["tickets"][0]["status"], "in_progress")

    def test_service_desk_configuration_controls_labels_categories_prefix_and_statuses(self):
        self._configure_helpdesk(
            {
                "helpdesk_display_label": "Facilities Helpdesk",
                "helpdesk_reference_prefix": "FAC",
                "helpdesk_category_options": "housing|Housing\nmaintenance|Facilities Maintenance",
                "helpdesk_status_labels": "submitted|Logged\naddressed|Triaged\nin_progress|Working\nsolved|Closed",
            }
        )

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/ict-helpdesk/student/tickets")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["title"], "Facilities Helpdesk")
        self.assertEqual(
            [option["value"] for option in response.json()["categories"]],
            ["housing", "maintenance"],
        )

        invalid = self.client.post(
            "/ict-helpdesk/student/tickets",
            {
                "category": "wifi",
                "subject": "Old category",
                "description": "This category has been removed.",
            },
            format="json",
        )
        self.assertEqual(invalid.status_code, 400, invalid.json())
        self.assertEqual(invalid.json()["detail"], "Select a valid Facilities Helpdesk category.")

        response = self.client.post(
            "/ict-helpdesk/student/tickets",
            {
                "category": "maintenance",
                "subject": "Leaking sink",
                "description": "The shared pantry sink is leaking.",
                "location": "Block C",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        payload = response.json()["ticket"]
        ticket = HelpdeskTicket.objects.get()
        self.assertEqual(payload["reference"], f"FAC-{ticket.id:05d}")
        self.assertEqual(payload["category_label"], "Facilities Maintenance")
        self.assertEqual(payload["status_label"], "Logged")

        self.client.force_authenticate(user=self.technician_user)
        dashboard = self.client.get("/ict-helpdesk/technician/dashboard")
        self.assertEqual(dashboard.status_code, 200, dashboard.json())
        self.assertEqual(dashboard.json()["title"], "Facilities Helpdesk")
        self.assertEqual(
            [option["label"] for option in dashboard.json()["statuses"]],
            ["Logged", "Triaged", "Working", "Closed"],
        )

        response = self.client.patch(
            f"/ict-helpdesk/technician/tickets/{ticket.id}",
            {"status": "in_progress", "note": "A facilities technician is on the way."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["ticket"]["status_label"], "Working")

    def test_category_assignment_rules_route_to_matching_technicians(self):
        other_department, _created = Department.objects.update_or_create(
            code="OPS",
            defaults={"name": "Operations Department", "school": None, "center": None},
        )
        other_user = User.objects.create_user(username="operations_technician", password="pass")
        other_profile = other_user.profile
        other_profile.role = Profile.ROLE_TECHNICIAN
        other_profile.department = other_department
        other_profile.save()
        Technician.objects.update_or_create(
            profile=other_profile,
            defaults={
                "technician_id": "OPS-001",
                "department": other_department,
                "is_active": True,
            },
        )

        self._configure_helpdesk(
            {
                "helpdesk_category_options": "wifi|Network\nfacilities|Facilities",
                "helpdesk_assignment_rules": "wifi|department|SUPPORT",
            }
        )

        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(
            "/ict-helpdesk/student/tickets",
            {
                "category": "wifi",
                "subject": "Network account locked",
                "description": "My account cannot join the campus network.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        ticket = HelpdeskTicket.objects.get()
        self.assertEqual(ticket.assigned_to, self.technician)
        self.assertTrue(Notification.objects.filter(recipient=self.technician, data__ticket_id=ticket.id).exists())
        self.assertFalse(Notification.objects.filter(recipient=other_profile, data__ticket_id=ticket.id).exists())

    def test_roles_cannot_cross_helpdesk_permissions(self):
        self.client.force_authenticate(user=self.student_user)
        self.assertEqual(self.client.get("/ict-helpdesk/technician/dashboard").status_code, 403)
        self.client.force_authenticate(user=self.technician_user)
        self.assertEqual(self.client.get("/ict-helpdesk/student/tickets").status_code, 403)

    def test_election_management_is_technician_only(self):
        admin_user = User.objects.create_superuser(
            username="election_admin",
            email="election-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=admin_user)
        self.assertEqual(self.client.get("/ict-helpdesk/technician/elections").status_code, 403)
        self.assertEqual(self.client.get("/admin/elections").status_code, 404)

        self.client.force_authenticate(user=self.technician_user)
        response = self.client.get("/ict-helpdesk/technician/elections")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["section"], "technician")

    def test_election_results_can_require_closed_voting(self):
        election = Election.objects.create(
            title="Student Council",
            election_type="student_council",
            election_type_label="Student council election",
            starts_at=timezone.now() - timezone.timedelta(hours=1),
            ends_at=timezone.now() + timezone.timedelta(hours=1),
            status=Election.STATUS_UPCOMING,
            is_active=True,
            seat_rules=[
                {
                    "key": "representatives",
                    "label": "Representatives",
                    "selection_count": 1,
                    "scope_type": Election.SEAT_SCOPE_CONSTITUENCY,
                }
            ],
            result_publication_rules={"publish_after_close": True},
        )

        self.client.force_authenticate(user=self.technician_user)
        response = self.client.post(
            "/ict-helpdesk/technician/elections/results",
            {"election": election.id},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        election.ends_at = timezone.now() - timezone.timedelta(minutes=1)
        election.save(update_fields=["ends_at", "updated_at"])
        response = self.client.post(
            "/ict-helpdesk/technician/elections/results",
            {"election": election.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())

    def test_admin_can_manage_technician_account(self):
        admin_user = User.objects.create_superuser(
            username="ict_admin",
            email="ict-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=admin_user)
        response = self.client.patch(
            f"/admin/manage/technicians?profile_id={self.technician.id}",
            {
                "designation": "Senior ICT Technician",
                "specialization": "Networks",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.technician.refresh_from_db()
        self.assertEqual(self.technician.department, self.department)
        self.assertIsNone(self.technician.center)
        self.assertEqual(self.technician.designation, "Senior ICT Technician")
        self.assertEqual(self.technician.technician_detail.specialization, "Networks")
