from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from admin_app.models import Profile
from auth_app.serializers import RegisterSerializer
from hr_app.models import CompensationChangeRequest, Employee, HRStaff, Position, SalaryAdjustment


User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class HrAppTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
        )
        self.hr_user = User.objects.create_user(
            username="hr",
            email="hr@example.com",
            password="StrongPass123!",
            first_name="Hana",
            last_name="HR",
        )
        self.hr_profile = self.hr_user.profile
        self.hr_profile.role = Profile.ROLE_HR
        self.hr_profile.staff_id = "HR-100"
        self.hr_profile.save()

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="StrongPass123!",
            first_name="Teacher",
            last_name="One",
        )
        self.teacher = self.teacher_user.profile
        self.teacher.role = Profile.ROLE_TEACHER
        self.teacher.staff_id = "TCH-100"
        self.teacher.save()

    def test_register_serializer_creates_hr_detail(self):
        serializer = RegisterSerializer(
            data={
                "username": "serializer-hr",
                "email": "serializer-hr@example.com",
                "first_name": "Serializer",
                "last_name": "HR",
                "password": "StrongPass123!",
                "role": Profile.ROLE_HR,
                "ums_id": "HR-200",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.role, Profile.ROLE_HR)
        self.assertTrue(HRStaff.objects.filter(profile=user.profile, hr_id="HR-200").exists())

    def test_hr_can_create_position_and_employee_master_record(self):
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.post(
            "/hr/positions",
            {
                "code": "LECT",
                "title": "Lecturer",
                "employment_type": "full_time",
                "grade": "A1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        position = Position.objects.get(code="LECT")

        response = self.client.post(
            "/hr/employees",
            {
                "profile_id": self.teacher.id,
                "employee_no": "EMP-100",
                "employment_status": "active",
                "position_id": position.id,
                "joining_date": "2026-07-08",
                "work_email": "teacher@aiu.edu.my",
                "salary_currency": "MYR",
                "base_salary": "5000.00",
                "current_salary": "5000.00",
                "current_bonus": "250.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        employee = Employee.objects.get(employee_no="EMP-100")
        self.assertEqual(employee.profile, self.teacher)
        self.assertEqual(employee.position, position)
        self.assertEqual(str(employee.current_salary), "5000.00")

        response = self.client.get(f"/hr/employees/{employee.id}")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["employee"]["current_salary"], "5000.00")
        self.assertEqual(response.json()["employee"]["current_bonus"], "250.00")
        self.assertIsNone(response.json()["employee"]["vacation_days_remaining"])
        self.assertTrue(response.json()["employee"]["is_placeholder"])
        self.assertEqual(len(response.json()["employee"]["employment_records"]), 1)

        response = self.client.post(
            f"/hr/employees/{employee.id}/compensation-requests",
            {
                "request_type": "salary",
                "change_type": "increase",
                "amount": "250.00",
                "effective_date": "2026-07-09",
                "reason": "Annual increment",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        employee.refresh_from_db()
        self.assertEqual(str(employee.current_salary), "5000.00")
        self.assertEqual(CompensationChangeRequest.objects.count(), 1)
        request_obj = CompensationChangeRequest.objects.get()
        self.assertEqual(request_obj.status, CompensationChangeRequest.STATUS_PENDING)
        self.assertEqual(str(request_obj.requested_amount), "5250.00")

        accountant_user = User.objects.create_user(username="accountant", password="StrongPass123!")
        accountant = accountant_user.profile
        accountant.role = Profile.ROLE_ACCOUNTANT
        accountant.staff_id = "ACC-100"
        accountant.save()
        self.client.force_authenticate(user=accountant_user)
        response = self.client.patch(
            "/finance/hr-compensation-requests",
            {"request_id": request_obj.id, "status": "approved", "review_note": "Budget approved"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        employee.refresh_from_db()
        self.assertEqual(str(employee.current_salary), "5250.00")
        self.assertEqual(SalaryAdjustment.objects.count(), 1)
        adjustment = SalaryAdjustment.objects.get()
        self.assertEqual(str(adjustment.previous_salary), "5000.00")
        self.assertEqual(str(adjustment.new_salary), "5250.00")

        self.client.force_authenticate(user=self.hr_user)
        response = self.client.post(
            f"/hr/employees/{employee.id}/compensation-requests",
            {
                "request_type": "bonus",
                "change_type": "increase",
                "amount": "300.00",
                "effective_date": "2026-07-10",
                "reason": "Performance bonus",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        bonus_request = CompensationChangeRequest.objects.order_by("-id").first()
        self.client.force_authenticate(user=accountant_user)
        response = self.client.patch(
            "/finance/hr-compensation-requests",
            {"request_id": bonus_request.id, "status": "approved"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        employee.refresh_from_db()
        self.assertEqual(str(employee.current_bonus), "550.00")

        self.client.force_authenticate(user=self.hr_user)
        response = self.client.post(
            f"/hr/employees/{employee.id}/compensation-requests",
            {"change_type": "decrease", "amount": "6000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.json())

        response = self.client.get("/hr/dashboard")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["summary"]["employees"], 1)
        self.assertEqual(response.json()["summary"]["monthly_payroll"], "5250.00")
        self.assertEqual(response.json()["summary"]["total_bonus"], "550.00")
        self.assertIsNone(response.json()["summary"]["vacation_days_available"])
        self.assertEqual(response.json()["statistics"]["status_counts"][1]["status"], "active")
        self.assertEqual(response.json()["statistics"]["status_counts"][1]["count"], 1)
        self.assertEqual(len(response.json()["statistics"]["recent_salary_adjustments"]), 1)

        response = self.client.get("/hr/statistics")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["summary"]["employees"], 1)
        self.assertEqual(response.json()["summary"]["leave_placeholder"], True)
        self.assertIsNone(response.json()["summary"]["vacation_days_remaining"])
        self.assertEqual(response.json()["charts"]["leave_placeholder"], [])
        self.assertEqual(response.json()["charts"]["salary_bands"][2]["count"], 1)

    def test_hr_cannot_access_transaction_audit(self):
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get("/hr/transactions")
        self.assertEqual(response.status_code, 404)
