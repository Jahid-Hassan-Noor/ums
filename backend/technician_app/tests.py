from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admin_app.models import Department, Profile
from auth_app.serializers import RegisterSerializer
from notifications_package.models import Notification
from technician_app.models import HelpdeskTicket, Technician


User = get_user_model()


class ICTHelpdeskWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department, _created = Department.objects.update_or_create(
            code="ICT",
            defaults={"name": "ICT Department", "school": None, "center": None},
        )

        self.technician_user = User.objects.create_user(username="technician", password="pass")
        self.technician = self.technician_user.profile
        self.technician.role = Profile.ROLE_TECHNICIAN
        self.technician.department = self.department
        self.technician.save()

        self.student_user = User.objects.create_user(username="student_helpdesk", password="pass")
        self.student = self.student_user.profile
        self.student.student_id = "STD-ICT-1"
        self.student.save(update_fields=["student_id", "updated_at"])

    def test_technician_account_is_created_under_standalone_ict_department(self):
        serializer = RegisterSerializer(
            data={
                "username": "new_technician",
                "email": "new-technician@example.com",
                "first_name": "New",
                "last_name": "Technician",
                "password": "StrongPass123!",
                "role": Profile.ROLE_TECHNICIAN,
                "ums_id": "ICT-100",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.department, self.department)
        self.assertIsNone(user.profile.center)
        self.assertIsNone(user.profile.school)
        self.assertIsNone(user.profile.unit)
        self.assertTrue(Technician.objects.filter(profile=user.profile, technician_id="ICT-100").exists())

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
