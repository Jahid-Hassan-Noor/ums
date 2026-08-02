from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accountant_app.models import (
    Accountant,
    FeeCategory,
    FinanceGatewayConfig,
    Fine,
    PaymentAttempt,
    StudentBalanceSnapshot,
    StudentCharge,
    StudentFinanceHold,
    StudentLedgerEntry,
    Subscription,
    SubscriptionPlan,
)
from accountant_app.tasks import mark_overdue_fines_task
from admin_app.models import Profile
from auth_app.serializers import RegisterSerializer
from notifications_package.models import Notification


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://frontend.test",
)
class FinanceSubscriptionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
        )
        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="StrongPass123!",
            first_name="Student",
            last_name="One",
        )
        self.student = self.student_user.profile
        self.student.student_id = "STD-100"
        self.student.save(update_fields=["updated_at"])
        self.student.student_detail.student_id = "STD-100"
        self.student.student_detail.save(update_fields=["student_id", "updated_at"])

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="StrongPass123!",
        )
        self.teacher = self.teacher_user.profile
        self.teacher.role = Profile.ROLE_TEACHER
        self.teacher.staff_id = "TCH-100"
        self.teacher.save()

        self.accountant_user = User.objects.create_user(
            username="accountant",
            email="accountant@example.com",
            password="StrongPass123!",
        )
        self.accountant = self.accountant_user.profile
        self.accountant.role = Profile.ROLE_ACCOUNTANT
        self.accountant.staff_id = "ACC-100"
        self.accountant.save()

        self.gym = SubscriptionPlan.objects.get(subscription_type=SubscriptionPlan.KIND_GYM)
        self.gym.price = Decimal("30.00")
        self.gym.save()
        self.kitchen = SubscriptionPlan.objects.get(subscription_type=SubscriptionPlan.KIND_KITCHEN)
        self.kitchen.price = Decimal("45.00")
        self.kitchen.save()
        FinanceGatewayConfig.objects.create(
            provider=FinanceGatewayConfig.PROVIDER_TOYYIBPAY,
            mode=FinanceGatewayConfig.MODE_SANDBOX,
            merchant_name="AIU Finance",
            api_base_url="https://payments.example.test/create",
            checkout_base_url="https://payments.example.test/pay",
            category_code="AIU-SUB",
            secret_key="secret-1234",
            callback_token="callback-123",
            is_active=True,
            updated_by=self.accountant,
        )

    def test_admin_can_create_and_manage_accountant(self):
        self.client.force_authenticate(user=self.admin_user)
        with patch("admin_app.views.admin_create_account.send_mail"):
            response = self.client.post(
                "/admin/create-account/accountant",
                {
                    "username": "new-accountant",
                    "email": "new-accountant@example.com",
                    "first_name": "New",
                    "last_name": "Accountant",
                    "password": "StrongPass123!",
                    "ums_id": "ACC-200",
                    "designation": "Finance Officer",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.json())
        profile = User.objects.get(username="new-accountant").profile
        self.assertEqual(profile.role, Profile.ROLE_ACCOUNTANT)
        self.assertTrue(Accountant.objects.filter(profile=profile, accountant_id="ACC-200").exists())

        response = self.client.patch(
            f"/admin/manage/accountants?profile_id={profile.id}",
            {"phone": "0123456789", "office_location": "Finance Counter", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        profile.refresh_from_db()
        profile.accountant_detail.refresh_from_db()
        self.assertEqual(profile.phone, "0123456789")
        self.assertEqual(profile.accountant_detail.office_location, "Finance Counter")

    def test_register_serializer_creates_accountant_detail(self):
        serializer = RegisterSerializer(
            data={
                "username": "serializer-accountant",
                "email": "serializer-accountant@example.com",
                "first_name": "Serializer",
                "last_name": "Accountant",
                "password": "StrongPass123!",
                "role": Profile.ROLE_ACCOUNTANT,
                "ums_id": "ACC-300",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.role, Profile.ROLE_ACCOUNTANT)
        self.assertEqual(user.profile.accountant_detail.accountant_id, "ACC-300")

    def test_accountant_can_update_gateway_and_plan_without_secret_echo(self):
        self.client.force_authenticate(user=self.accountant_user)
        response = self.client.patch(
            "/finance/gateway",
            {
                "provider": "toyyibpay",
                "mode": "production",
                "merchant_name": "AIU Finance Live",
                "api_base_url": "https://duitnow.example.test/create",
                "checkout_base_url": "https://duitnow.example.test/pay",
                "category_code": "LIVE",
                "secret_key": "live-secret",
                "callback_token": "live-callback",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        gateway = response.json()["gateway"]
        self.assertTrue(gateway["secret_key_present"])
        self.assertNotIn("live-secret", str(gateway))

        response = self.client.patch(
            "/finance/plans",
            {
                "plan_id": self.gym.id,
                "name": "Gym Subscription",
                "description": "Gym",
                "price": "35.00",
                "duration_days": 45,
                "is_active": True,
                "available_to_all_roles": False,
                "available_roles": [Profile.ROLE_STUDENT, Profile.ROLE_TEACHER],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.gym.refresh_from_db()
        self.assertEqual(self.gym.price, Decimal("35.00"))
        self.assertEqual(self.gym.duration_days, 45)
        self.assertFalse(self.gym.available_to_all_roles)
        self.assertEqual(self.gym.available_roles, [Profile.ROLE_STUDENT, Profile.ROLE_TEACHER])

    def test_accountant_can_create_and_delete_flexible_subscription_option(self):
        self.client.force_authenticate(user=self.accountant_user)
        response = self.client.post(
            "/finance/plans",
            {
                "name": "Campus WiFi",
                "subscription_type": "campus-wifi",
                "description": "WiFi access package",
                "price": "12.50",
                "duration_days": 14,
                "is_active": True,
                "available_to_all_roles": False,
                "available_roles": [Profile.ROLE_STUDENT, Profile.ROLE_ADMIN],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        plan = SubscriptionPlan.objects.get(subscription_type="campus-wifi")
        self.assertEqual(plan.available_roles, [Profile.ROLE_STUDENT, Profile.ROLE_ADMIN])

        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get("/finance/my-subscriptions")
        self.assertNotIn(plan.id, [item["id"] for item in response.json()["plans"]])

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/finance/my-subscriptions")
        self.assertIn(plan.id, [item["id"] for item in response.json()["plans"]])

        self.client.force_authenticate(user=self.accountant_user)
        response = self.client.delete("/finance/plans", {"plan_id": plan.id}, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()["deleted"])
        self.assertFalse(SubscriptionPlan.objects.filter(pk=plan.id).exists())

    def test_accountant_can_post_student_charge_and_finance_hold(self):
        self.client.force_authenticate(user=self.accountant_user)
        response = self.client.post(
            "/finance/fee-categories",
            {
                "code": "TUITION",
                "name": "Tuition Fees",
                "description": "Semester tuition charges",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        category = FeeCategory.objects.get(code="TUITION")

        response = self.client.post(
            "/finance/student-ledgers",
            {
                "student_id": self.student.id,
                "category_id": category.id,
                "description": "Semester 1 tuition",
                "amount": "1200.00",
                "due_date": "2026-08-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertTrue(StudentCharge.objects.filter(student=self.student, category=category).exists())
        entry = StudentLedgerEntry.objects.get(student=self.student, entry_type=StudentLedgerEntry.ENTRY_DEBIT)
        self.assertEqual(entry.balance_after, Decimal("1200.00"))
        self.assertEqual(StudentBalanceSnapshot.objects.get(student=self.student).balance, Decimal("1200.00"))

        response = self.client.post(
            "/finance/holds",
            {
                "student_id": self.student.id,
                "reason": "Outstanding tuition balance",
                "notes": "Generated by finance counter",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        hold = StudentFinanceHold.objects.get(student=self.student)
        self.assertTrue(hold.is_active)

        response = self.client.patch("/finance/holds", {"hold_id": hold.id}, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        hold.refresh_from_db()
        self.assertFalse(hold.is_active)

    def test_fine_lifecycle_posts_and_settles_student_ledger(self):
        self.client.force_authenticate(user=self.accountant_user)
        with patch("accountant_app.fine_service._create_fine_payment_link", return_value=""):
            response = self.client.post(
                "/finance/fines",
                {
                    "student_id": self.student.id,
                    "reason": "Lost library card",
                    "amount": "25.00",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.json())
        fine = Fine.objects.get(reason="Lost library card")
        charge = StudentCharge.objects.get(source_type=StudentCharge.SOURCE_FINE, source_id=fine.id)
        debit = StudentLedgerEntry.objects.get(charge=charge, entry_type=StudentLedgerEntry.ENTRY_DEBIT)
        self.assertEqual(debit.balance_after, Decimal("25.00"))

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f"/finance/fines/{fine.id}/deduct", {"note": "Meal allowance"}, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        payment = StudentLedgerEntry.objects.get(charge=charge, entry_type=StudentLedgerEntry.ENTRY_PAYMENT)
        self.assertEqual(payment.balance_after, Decimal("0.00"))

    @override_settings(PUBLIC_BACKEND_BASE_URL="https://api.portal.example.edu")
    def test_subscription_checkout_uses_public_backend_base_for_gateway_urls(self):
        captured_payload = {}

        def fake_gateway_post(url, payload):
            captured_payload.update(payload)
            return '[{"BillCode": "BILL-PUBLIC"}]'

        self.client.force_authenticate(user=self.student_user)
        with patch("accountant_app.service._post_form", side_effect=fake_gateway_post):
            response = self.client.post(
                "/finance/subscriptions/purchase",
                {"plan_id": self.gym.id},
                format="json",
            )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(
            captured_payload["billReturnUrl"],
            "https://api.portal.example.edu/finance/payments/return",
        )
        self.assertEqual(
            captured_payload["billCallbackUrl"],
            "https://api.portal.example.edu/finance/payments/webhook?token=callback-123",
        )

    def test_student_payment_webhook_activates_subscription_and_card(self):
        self.client.force_authenticate(user=self.student_user)
        with patch(
            "accountant_app.service._create_gateway_checkout",
            return_value={
                "raw": [{"BillCode": "BILL-1"}],
                "gateway_reference": "BILL-1",
                "checkout_url": "https://payments.example.test/pay/BILL-1",
            },
        ):
            response = self.client.post(
                "/finance/subscriptions/purchase",
                {"plan_id": self.gym.id},
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.json())
        attempt = PaymentAttempt.objects.get(gateway_reference="BILL-1")

        self.client.force_authenticate(user=None)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/finance/payments/webhook?token=callback-123",
                {"status": "1", "billcode": "BILL-1", "order_id": attempt.external_reference},
            )
        self.assertEqual(response.status_code, 200, response.json())
        subscription = Subscription.objects.get()
        self.assertEqual(subscription.status, Subscription.STATUS_ACTIVE)
        self.assertIsNotNone(subscription.ends_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].attachments)

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(f"/finance/subscriptions/{subscription.id}/card")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_subscription_plan_roles_define_purchase_eligibility(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.post(
            "/finance/subscriptions/purchase",
            {"plan_id": self.kitchen.id},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("not eligible", response.json()["detail"])

        self.client.force_authenticate(user=self.accountant_user)
        response = self.client.patch(
            "/finance/plans",
            {
                "plan_id": self.kitchen.id,
                "available_to_all_roles": False,
                "available_roles": [Profile.ROLE_TEACHER],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        self.client.force_authenticate(user=self.teacher_user)
        with patch(
            "accountant_app.service._create_gateway_checkout",
            return_value={
                "raw": [{"BillCode": "BILL-KITCHEN-TEACHER"}],
                "gateway_reference": "BILL-KITCHEN-TEACHER",
                "checkout_url": "https://payments.example.test/pay/BILL-KITCHEN-TEACHER",
            },
        ):
            response = self.client.post(
                "/finance/subscriptions/purchase",
                {"plan_id": self.kitchen.id},
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.json())


class FineTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student_user = User.objects.create_user(
            username="student_fine",
            email="student_fine@example.com",
            password="StrongPass123!",
            first_name="Student",
            last_name="Fine",
        )
        self.student = self.student_user.profile
        self.student.student_id = "STD-200"
        self.student.save()
        self.student.student_detail.student_id = "STD-200"
        self.student.student_detail.save()

        self.accountant_user = User.objects.create_user(
            username="accountant_fine",
            email="accountant_fine@example.com",
            password="StrongPass123!",
        )
        self.accountant_profile = self.accountant_user.profile
        self.accountant_profile.role = Profile.ROLE_ACCOUNTANT
        self.accountant_profile.save()
        self.accountant = Accountant.objects.filter(profile=self.accountant_profile).first()
        if self.accountant:
            self.accountant.accountant_id = "ACC-200"
            self.accountant.save()
        else:
            self.accountant = Accountant.objects.create(
                profile=self.accountant_profile,
                accountant_id="ACC-200",
            )

        # Configure active gateway
        self.gateway = FinanceGatewayConfig.objects.create(
            provider="toyyibpay",
            mode="sandbox",
            merchant_name="AIU Sandbox",
            api_base_url="https://payments.example.test/create",
            checkout_base_url="https://payments.example.test/pay",
            category_code="CAT123",
            secret_key="my-secret-key",
            callback_token="callback-123",
            is_active=True,
        )

    def test_create_fine_api_success(self):
        self.client.force_authenticate(user=self.accountant_user)
        with patch(
            "accountant_app.service._create_gateway_checkout",
            return_value={
                "raw": [{"BillCode": "BILL-FINE-1"}],
                "gateway_reference": "BILL-FINE-1",
                "checkout_url": "https://payments.example.test/pay/BILL-FINE-1",
            },
        ):
            response = self.client.post(
                "/finance/fines",
                {
                    "student_id": self.student.id,
                    "reason": "Broken window in hostel",
                    "amount": "50.00",
                    "description": "Student broke window in room 101",
                    "due_date": "2026-07-10T23:59:00Z",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        fine_data = response.json()["fine"]
        self.assertEqual(fine_data["reason"], "Broken window in hostel")
        self.assertEqual(fine_data["amount"], "50.00")
        self.assertEqual(fine_data["status"], "pending")
        self.assertEqual(fine_data["checkout_url"], "https://payments.example.test/pay/BILL-FINE-1")

    @override_settings(PUBLIC_BACKEND_BASE_URL="https://api.portal.example.edu")
    def test_fine_checkout_uses_public_backend_base_for_gateway_urls(self):
        captured_payload = {}

        def fake_gateway_post(url, payload):
            captured_payload.update(payload)
            return '[{"BillCode": "BILL-FINE-PUBLIC"}]'

        self.client.force_authenticate(user=self.accountant_user)
        with patch("accountant_app.service._post_form", side_effect=fake_gateway_post):
            response = self.client.post(
                "/finance/fines",
                {
                    "student_id": self.student.id,
                    "reason": "Replacement card",
                    "amount": "15.00",
                    "description": "Lost ID replacement",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(
            captured_payload["billReturnUrl"],
            "https://api.portal.example.edu/finance/payments/return",
        )
        self.assertEqual(
            captured_payload["billCallbackUrl"],
            "https://api.portal.example.edu/finance/payments/webhook?token=callback-123",
        )

    def test_student_list_own_fines(self):
        Fine.objects.create(
            student=self.student,
            issued_by=self.accountant,
            reason="Late library return",
            amount=Decimal("10.00"),
        )
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/finance/my-fines")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["fines"]), 1)
        self.assertEqual(response.json()["fines"][0]["reason"], "Late library return")

    def test_manual_deduction_notifies_student(self):
        fine = Fine.objects.create(
            student=self.student,
            issued_by=self.accountant,
            reason="Unpaid kitchen charge",
            amount=Decimal("30.00"),
        )
        self.client.force_authenticate(user=self.accountant_user)
        response = self.client.post(
            f"/finance/fines/{fine.id}/deduct",
            {"note": "Deducted from July allowance"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.STATUS_DEDUCTED)
        self.assertEqual(fine.deduction_note, "Deducted from July allowance")

    def test_payment_webhook_updates_fine(self):
        fine = Fine.objects.create(
            student=self.student,
            issued_by=self.accountant,
            reason="ID replacement fee",
            amount=Decimal("25.00"),
            gateway_bill_code="BILL-FINE-99",
        )
        response = self.client.post(
            "/finance/payments/webhook?token=callback-123",
            {"status": "1", "billcode": "BILL-FINE-99", "order_id": f"FINE-{fine.pk}-RANDOM"},
        )
        self.assertEqual(response.status_code, 200)
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.STATUS_PAID)
        self.assertIsNotNone(fine.paid_at)

    def test_overdue_fine_task_marks_pending_fines_and_notifies_student(self):
        overdue_fine = Fine.objects.create(
            student=self.student,
            issued_by=self.accountant,
            reason="Late library return",
            amount=Decimal("10.00"),
            due_date=timezone.now() - timezone.timedelta(days=1),
        )
        future_fine = Fine.objects.create(
            student=self.student,
            issued_by=self.accountant,
            reason="Future replacement fee",
            amount=Decimal("15.00"),
            due_date=timezone.now() + timezone.timedelta(days=1),
        )

        result = mark_overdue_fines_task.call()

        self.assertEqual(result, {"overdue_fines_flagged": 1})
        overdue_fine.refresh_from_db()
        future_fine.refresh_from_db()
        self.assertEqual(overdue_fine.status, Fine.STATUS_OVERDUE)
        self.assertEqual(future_fine.status, Fine.STATUS_PENDING)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="fine_overdue",
                data__fine_id=overdue_fine.pk,
            ).exists()
        )

    def test_overdue_fine_task_does_not_notify_already_overdue_fines(self):
        fine = Fine.objects.create(
            student=self.student,
            issued_by=self.accountant,
            reason="Already overdue charge",
            amount=Decimal("12.00"),
            due_date=timezone.now() - timezone.timedelta(days=2),
            status=Fine.STATUS_OVERDUE,
        )

        result = mark_overdue_fines_task.call()

        self.assertEqual(result, {"overdue_fines_flagged": 0})
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="fine_overdue",
                data__fine_id=fine.pk,
            ).exists()
        )
