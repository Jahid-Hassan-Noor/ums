from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accountant_app.fine_views import StudentFineInitiatePayment, StudentFineList
from accountant_app.ledger_views import FinanceStudentBalance
from accountant_app.views import (
    MySubscriptions,
    PaymentReturn,
    PaymentWebhook,
    SubscriptionCard,
    SubscriptionPurchase,
)
from auth_app.auth_tokens import SESSION_EXP_CLAIM, issue_ums_refresh
from admin_app.models import Profile
from auth_app.permissions import (
    IsActiveUmsUser,
    IsAdminRole,
    IsAccountantRole,
    IsApplicantRole,
    IsApplicantStaffRole,
    IsCatererRole,
    IsExecutiveRole,
    IsHrRole,
    IsLibrarianRole,
    IsStudentRole,
    IsTeacherRole,
    IsTechnicianRole,
)
from auth_app.views.account import (
    ChangePasswordView,
    ForgotPasswordView,
    LoginView,
    MeView,
    RegisterView,
    ResetPasswordView,
    SendEmailVerificationView,
    UmsTokenRefreshSerializer,
    UmsTokenRefreshView,
    VerifyEmailView,
)
from notifications_package.views import NotificationSummaryView
from applicant_app.views.applicant_auth import (
    ApplicantLoginView,
    ApplicantMeView,
    ApplicantRegisterView,
)
from applicant_app.views.applicant_options import ApplicantOptionsView
from applicant_app.views.applicant_staff import (
    StaffApplicationCollectionView,
    StaffApplicationDocumentReviewView,
    StaffApplicationStatusView,
    StaffScholarshipReviewView,
)
from home_app.views.public_notifications import PublicNotifications
from home_app.views.public_profile import PublicProfile


User = get_user_model()
NO_THROTTLE_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


def remote_addr_for_test(name):
    last_octet = (sum(ord(char) for char in name) % 200) + 10
    return f"10.242.0.{last_octet}"


def api_routes(patterns=None):
    patterns = patterns or get_resolver().url_patterns
    for entry in patterns:
        if isinstance(entry, URLResolver):
            yield from api_routes(entry.url_patterns)
            continue
        if not isinstance(entry, URLPattern):
            continue
        callback = entry.callback
        view_class = getattr(callback, "cls", None)
        if not view_class or not issubclass(view_class, APIView):
            continue
        initkwargs = getattr(callback, "initkwargs", {})
        permissions = list(
            initkwargs.get(
                "permission_classes",
                view_class.permission_classes,
            )
        )
        yield view_class, permissions


class RoutePermissionPolicyTests(SimpleTestCase):
    public_account_views = {
        LoginView,
        ForgotPasswordView,
        ResetPasswordView,
        ApplicantLoginView,
        ApplicantRegisterView,
        ApplicantOptionsView,
    }
    active_portal_views = {
        ChangePasswordView,
        MeView,
        NotificationSummaryView,
        SendEmailVerificationView,
        VerifyEmailView,
        PublicNotifications,
        PublicProfile,
    }
    applicant_staff_views = {
        StaffApplicationCollectionView,
        StaffApplicationDocumentReviewView,
        StaffApplicationStatusView,
        StaffScholarshipReviewView,
    }
    accountant_active_ums_views = {
        FinanceStudentBalance,
        MySubscriptions,
        StudentFineInitiatePayment,
        StudentFineList,
        SubscriptionCard,
        SubscriptionPurchase,
    }
    accountant_public_views = {
        PaymentReturn,
        PaymentWebhook,
    }

    def expected_permission(self, view_class):
        if view_class in self.public_account_views:
            return AllowAny
        if view_class in self.active_portal_views:
            return IsActiveUmsUser
        if view_class is RegisterView:
            return IsAdminRole
        if view_class in self.applicant_staff_views:
            return IsApplicantStaffRole
        if view_class in self.accountant_active_ums_views:
            return IsActiveUmsUser
        if view_class in self.accountant_public_views:
            return AllowAny
        if view_class is ApplicantMeView:
            return IsApplicantRole

        module = view_class.__module__
        if module.startswith("home_app.views."):
            return AllowAny
        if module.startswith("chatbot_app."):
            return AllowAny
        if module == "core.media_access":
            return AllowAny
        if module == "drf_spectacular.views":
            return IsAdminRole
        if module.startswith("notifications_package.views"):
            return IsActiveUmsUser
        if module.startswith("admin_app.views."):
            return IsAdminRole
        if module.startswith("accountant_app."):
            return IsAccountantRole
        if module.startswith("applicant_app.views."):
            return IsApplicantRole
        if module.startswith("caterer_app.views."):
            return IsCatererRole
        if module.startswith("executive_app.views."):
            return IsExecutiveRole
        if module.startswith("gradebook_app."):
            if view_class.__name__.startswith("Admin"):
                return IsAdminRole
            if view_class.__name__.startswith("Teacher"):
                return IsTeacherRole
            if view_class.__name__.startswith("Student"):
                return IsStudentRole
        if module.startswith("hr_app."):
            return IsActiveUmsUser if view_class.__name__ == "HrMyProfile" else IsHrRole
        if module.startswith("librarian_app.views."):
            return IsLibrarianRole
        if module.startswith("quiz_app."):
            return (
                IsTeacherRole
                if view_class.__name__.startswith("Teacher")
                else IsStudentRole
            )
        if module.startswith("student_app.views."):
            return IsStudentRole
        if module.startswith("teacher_app.views."):
            return IsTeacherRole
        if module.startswith("technician_app.views."):
            return (
                IsStudentRole
                if view_class.__name__ == "StudentHelpdeskTickets"
                else IsTechnicianRole
            )
        self.fail(f"Unclassified API view: {module}.{view_class.__name__}")

    def test_every_registered_api_route_has_an_explicit_security_policy(self):
        checked = 0
        for view_class, permissions in api_routes():
            if view_class is UmsTokenRefreshView:
                self.assertIs(
                    view_class.serializer_class,
                    UmsTokenRefreshSerializer,
                )
                checked += 1
                continue

            expected = self.expected_permission(view_class)
            self.assertEqual(
                permissions,
                [expected],
                f"{view_class.__module__}.{view_class.__name__}",
            )
            checked += 1

        self.assertGreater(checked, 200)


@override_settings(REST_FRAMEWORK=NO_THROTTLE_REST_FRAMEWORK)
class ActivePortalAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.defaults["REMOTE_ADDR"] = remote_addr_for_test(
            self._testMethodName
        )
        self.user = User.objects.create_user(
            username="security_user",
            password="StrongPass123!",
        )

    def test_portal_jwt_settings_keep_one_week_refresh_without_long_lived_access(self):
        jwt_settings = settings.SIMPLE_JWT

        self.assertGreater(jwt_settings["ACCESS_TOKEN_LIFETIME"], timedelta())
        self.assertLessEqual(jwt_settings["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=5))
        self.assertEqual(jwt_settings["REFRESH_TOKEN_LIFETIME"], timedelta(days=7))
        self.assertTrue(jwt_settings["ROTATE_REFRESH_TOKENS"])
        self.assertTrue(jwt_settings["BLACKLIST_AFTER_ROTATION"])

    def test_login_tokens_carry_absolute_one_week_session_expiry(self):
        response = self.client.post(
            "/auth/login",
            {"username": self.user.username, "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        refresh = RefreshToken(payload["refresh"])
        access = AccessToken(payload["access"])
        session_seconds = int(timedelta(days=7).total_seconds())

        self.assertEqual(refresh[SESSION_EXP_CLAIM], refresh["exp"])
        self.assertEqual(access[SESSION_EXP_CLAIM], refresh[SESSION_EXP_CLAIM])
        self.assertEqual(refresh[SESSION_EXP_CLAIM] - refresh["iat"], session_seconds)

    def test_refresh_rotation_keeps_absolute_session_expiry_and_blacklists_old_token(self):
        refresh = issue_ums_refresh(self.user)
        original_refresh_token = str(refresh)
        original_session_expiry = refresh[SESSION_EXP_CLAIM]

        response = self.client.post(
            "/auth/token/refresh",
            {"refresh": original_refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        rotated_refresh = RefreshToken(payload["refresh"])
        rotated_access = AccessToken(payload["access"])

        self.assertNotEqual(rotated_refresh["jti"], refresh["jti"])
        self.assertEqual(rotated_refresh[SESSION_EXP_CLAIM], original_session_expiry)
        self.assertEqual(rotated_access[SESSION_EXP_CLAIM], original_session_expiry)
        self.assertLessEqual(rotated_refresh["exp"], original_session_expiry)
        self.assertLessEqual(rotated_access["exp"], original_session_expiry)

        reused_response = self.client.post(
            "/auth/token/refresh",
            {"refresh": original_refresh_token},
            format="json",
        )
        self.assertEqual(reused_response.status_code, 401)

    def test_login_rejects_an_inactive_portal_profile(self):
        self.user.profile.is_active = False
        self.user.profile.save(update_fields=["is_active", "updated_at"])

        response = self.client.post(
            "/auth/login",
            {"username": self.user.username, "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_refresh_rejects_a_token_after_the_portal_profile_is_disabled(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.user.profile.is_active = False
        self.user.profile.save(update_fields=["is_active", "updated_at"])

        response = self.client.post(
            "/auth/token/refresh",
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_active_profile_is_required_for_general_authenticated_routes(self):
        self.client.force_authenticate(user=self.user)
        self.user.profile.is_active = False
        self.user.profile.save(update_fields=["is_active", "updated_at"])

        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 403)
