from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from admin_app.models import Center, Profile, Unit
from auth_app.serializers import RegisterSerializer
from caterer_app.models import (
    Caterer,
    CanteenBalanceAdjustment,
    CanteenMonthlyBonus,
    CanteenTransaction,
    StudentCanteenAccount,
)
from caterer_app.service import allowance_month, dashboard_summary, deduct, ensure_account, initialize_accounts
from student_app.models import Student


User = get_user_model()


class CanteenWorkflowTests(TestCase):
    def student_canteen_balance(self, profile):
        return Student.objects.filter(profile_id=profile.id).values_list("canteen_balance", flat=True).get()

    def setUp(self):
        self.client = APIClient()
        self.center = Center.objects.create(code="CSAA", name="Centre for Student Affairs and Alumni")
        self.unit = Unit.objects.create(code="CTN-ADMIN", name="Canteen Admin", center=self.center)

        self.caterer_user = User.objects.create_user(username="caterer", password="pass")
        self.caterer = self.caterer_user.profile
        self.caterer.role = Profile.ROLE_CATERER
        self.caterer.center = self.center
        self.caterer.unit = self.unit
        self.caterer.save()
        self.caterer.caterer_detail.caterer_id = "CAT-1"
        self.caterer.caterer_detail.save(update_fields=["caterer_id", "updated_at"])

        self.student_user = User.objects.create_user(username="student", password="pass")
        self.student = self.student_user.profile
        self.student.student_id = "STD-100"
        self.student.save(update_fields=["student_id", "updated_at"])
        self.student.student_detail.student_id = "STD-100"
        self.student.student_detail.enrollment_status = "active"
        self.student.student_detail.save()

    def test_caterer_account_is_created_under_csaa(self):
        serializer = RegisterSerializer(
            data={
                "username": "new_caterer",
                "email": "new-caterer@example.com",
                "first_name": "New",
                "last_name": "Caterer",
                "password": "StrongPass123!",
                "role": Profile.ROLE_CATERER,
                "ums_id": "CAT-100",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.center, self.center)
        self.assertEqual(user.profile.unit, self.unit)
        self.assertTrue(Caterer.objects.filter(profile=user.profile, caterer_id="CAT-100").exists())

    def test_allowance_month_switches_at_first_day_8am(self):
        zone = ZoneInfo("Asia/Kuala_Lumpur")
        self.assertEqual(
            allowance_month(datetime(2026, 7, 1, 7, 59, tzinfo=zone)).isoformat(),
            "2026-06-01",
        )
        self.assertEqual(
            allowance_month(datetime(2026, 7, 1, 8, 0, tzinfo=zone)).isoformat(),
            "2026-07-01",
        )

    def test_active_student_receives_allowance_and_caterer_can_deduct(self):
        account = ensure_account(self.student)
        self.assertEqual(account.allowance_amount, Decimal("50.00"))
        self.assertEqual(self.student_canteen_balance(self.student), Decimal("50.00"))

        CanteenMonthlyBonus.objects.create(month=account.month, extra_amount=Decimal("10.00"), occasion="Eid")
        account = ensure_account(self.student)
        self.assertEqual(account.allowance_amount, Decimal("60.00"))
        self.assertEqual(self.student_canteen_balance(self.student), Decimal("60.00"))

        account, transaction = deduct(self.student, self.caterer, Decimal("12.50"), "Lunch")
        self.assertEqual(account.balance, Decimal("47.50"))
        self.assertEqual(transaction.amount, Decimal("12.50"))
        self.assertEqual(self.student_canteen_balance(self.student), Decimal("47.50"))

    def test_monthly_allowance_is_allocated_in_full_to_each_active_student(self):
        second_user = User.objects.create_user(username="student-2", password="pass")
        second_student = second_user.profile
        second_student.student_id = "STD-200"
        second_student.save(update_fields=["student_id", "updated_at"])
        second_student.student_detail.student_id = "STD-200"
        second_student.student_detail.enrollment_status = "active"
        second_student.student_detail.save()

        result = initialize_accounts()
        accounts = StudentCanteenAccount.objects.filter(month=result["month"]).order_by("student_id")

        self.assertEqual(result["created"], 2)
        self.assertEqual(accounts.count(), 2)
        self.assertEqual(
            list(accounts.values_list("allowance_amount", flat=True)),
            [Decimal("50.00"), Decimal("50.00")],
        )
        self.assertEqual(self.student_canteen_balance(self.student), Decimal("50.00"))
        self.assertEqual(self.student_canteen_balance(second_student), Decimal("50.00"))
        self.assertEqual(dashboard_summary()["allocated"], "100.00")

    def test_inactive_student_statuses_are_ineligible(self):
        for enrollment_status in ("internship", "terminated", "graduated", "dropout"):
            detail = self.student.student_detail
            detail.enrollment_status = enrollment_status
            detail.save(update_fields=["enrollment_status", "updated_at"])
            with self.assertRaises(ValidationError):
                ensure_account(self.student)

    def test_caterer_api_searches_and_deducts_by_student_id(self):
        self.client.force_authenticate(user=self.caterer_user)
        response = self.client.get("/canteen/student", {"student_id": "STD-100"})
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["account"]["balance"], "50.00")

        response = self.client.post(
            "/canteen/transactions",
            {"student_id": "STD-100", "amount": "9.90", "description": "Breakfast"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["account"]["balance"], "40.10")
        self.assertEqual(CanteenTransaction.objects.count(), 1)

    def test_student_role_cannot_use_caterer_api(self):
        self.client.force_authenticate(user=self.student_user)
        self.assertEqual(self.client.get("/canteen/dashboard").status_code, 403)

    def test_student_dashboard_shows_own_canteen_balance_and_transactions(self):
        deduct(self.student, self.caterer, Decimal("12.50"), "Lunch")
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get("/student/dashboard")

        self.assertEqual(response.status_code, 200, response.json())
        account = response.json()["canteen_account"]
        self.assertEqual(account["student"]["student_id"], "STD-100")
        self.assertEqual(account["allowance_amount"], "50.00")
        self.assertEqual(account["spent_amount"], "12.50")
        self.assertEqual(account["balance"], "37.50")
        self.assertEqual(len(account["transactions"]), 1)

    def test_caterer_cannot_add_student_balance(self):
        self.client.force_authenticate(user=self.caterer_user)
        response = self.client.post(
            "/admin/canteen",
            {"student_id": "STD-100", "amount": "20.00", "reason": "Not allowed"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CanteenBalanceAdjustment.objects.count(), 0)

    def test_admin_manages_caterer_but_accountant_manages_allowance(self):
        admin_user = User.objects.create_superuser(
            username="canteen_admin",
            email="canteen-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=admin_user)

        response = self.client.patch(
            f"/admin/manage/caterers?profile_id={self.caterer.id}",
            {"designation": "Canteen Supervisor", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.caterer.caterer_detail.refresh_from_db()
        self.assertEqual(self.caterer.caterer_detail.designation, "Canteen Supervisor")

        account = ensure_account(self.student)
        response = self.client.patch(
            "/admin/canteen",
            {"monthly_allowance": "55.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 403, response.json())

        accountant_user = User.objects.create_user(username="accountant", password="pass")
        accountant = accountant_user.profile
        accountant.role = Profile.ROLE_ACCOUNTANT
        accountant.staff_id = "ACC-100"
        accountant.save()
        self.client.force_authenticate(user=accountant_user)

        response = self.client.patch(
            "/finance/canteen",
            {
                "monthly_allowance": "55.00",
                "month": account.month.isoformat(),
                "extra_amount": "5.00",
                "occasion": "Eid",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        account.refresh_from_db()
        self.assertEqual(account.allowance_amount, Decimal("60.00"))
        self.assertTrue(
            self.caterer.notifications.filter(data__event_type="canteen.policy_updated").exists()
        )
        self.assertTrue(
            self.student.notifications.filter(data__event_type="canteen.allowance_updated").exists()
        )

        response = self.client.post(
            "/finance/canteen",
            {
                "student_id": "STD-100",
                "amount": "15.00",
                "reason": "Emergency meal support",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["account"]["adjustment_amount"], "15.00")
        self.assertEqual(response.json()["account"]["balance"], "75.00")
        self.assertEqual(CanteenBalanceAdjustment.objects.count(), 1)
        self.assertEqual(self.student_canteen_balance(self.student), Decimal("75.00"))
        self.assertTrue(
            self.student.notifications.filter(data__event_type="canteen.balance_adjusted").exists()
        )

        account = ensure_account(self.student)
        self.assertEqual(account.balance, Decimal("75.00"))
