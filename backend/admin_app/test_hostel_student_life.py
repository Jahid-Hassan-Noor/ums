from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admin_app.models import Profile, SystemSetting


User = get_user_model()


class HostelStudentLifeTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="hostel_admin",
            password="StrongPass123!",
        )
        self.admin_user.profile.role = Profile.ROLE_ADMIN
        self.admin_user.profile.save(update_fields=["role", "updated_at"])

        self.student_user = User.objects.create_user(
            username="hostel_student",
            password="StrongPass123!",
        )

        self.client = APIClient()

    def test_admin_update_controls_student_contact_and_schedule_payloads(self):
        self.client.force_authenticate(self.admin_user)
        payload = {
            "emergency_contacts": [
                {
                    "label": "Student Affairs Duty Desk",
                    "phone": "+604 774 7300",
                    "email": "student.affairs@example.edu",
                    "available_hours": "24 hours",
                    "notes": "Call this line for urgent hostel support.",
                }
            ],
            "warden_schedule": [
                {
                    "day": "Monday",
                    "time_range": "8:00 PM - 11:00 PM",
                    "warden_name": "Ms. Aisha",
                    "phone": "+6012 345 6789",
                    "location": "Hostel 25A lobby",
                    "notes": "Night round duty.",
                }
            ],
        }

        update_response = self.client.patch(
            "/admin/hostels/student-life",
            {"student_life": payload},
            format="json",
        )

        self.assertEqual(update_response.status_code, 200)
        setting = SystemSetting.objects.get(key="hostel.student_life")
        self.assertTrue(setting.is_public)
        self.assertEqual(setting.value["emergency_contacts"][0]["label"], "Student Affairs Duty Desk")

        self.client.force_authenticate(self.student_user)
        contacts_response = self.client.get("/student/emergency-contacts")
        schedule_response = self.client.get("/student/warden-schedule")

        self.assertEqual(contacts_response.status_code, 200)
        self.assertEqual(schedule_response.status_code, 200)
        self.assertEqual(
            contacts_response.data["contacts"][0]["phone"],
            "+604 774 7300",
        )
        self.assertEqual(
            schedule_response.data["schedule"][0]["warden_name"],
            "Ms. Aisha",
        )

    def test_admin_update_rejects_incomplete_contact_rows(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            "/admin/hostels/student-life",
            {
                "student_life": {
                    "emergency_contacts": [{"label": "Duty Desk"}],
                    "warden_schedule": [],
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("emergency_contacts", response.data)
        self.assertFalse(SystemSetting.objects.filter(key="hostel.student_life").exists())
