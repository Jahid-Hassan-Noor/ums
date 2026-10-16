import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenRefreshView

from admin_app.settings_registry import (
    feature_enabled,
    maintenance_mode_enabled,
    portal_name,
    role_module_enabled,
)
from auth_app.auth_tokens import (
    cap_token_to_ums_session,
    issue_ums_refresh,
    rotate_refresh_with_ums_session,
    session_seconds_remaining,
)
from auth_app.models import Profile
from auth_app.permissions import (
    IsActiveUmsUser,
    IsAdminRole,
    profile_role_for_user,
)
from auth_app.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ProfilePictureUpdateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    managed_hostel_room,
)


User = get_user_model()
logger = logging.getLogger(__name__)


class MaintenanceModeUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The UMS is currently in maintenance mode."
    default_code = "maintenance_mode"


def _maintenance_blocks_user(user):
    return (
        maintenance_mode_enabled()
        and profile_role_for_user(user) != Profile.ROLE_ADMIN
    )


def _enforce_maintenance_access(user):
    if _maintenance_blocks_user(user):
        raise MaintenanceModeUnavailable()


def _login_username_for_identifier(identifier):
    identifier = str(identifier).strip()
    if not identifier or "@" not in identifier:
        return identifier

    matches = list(
        User.objects.filter(email__iexact=identifier)
        .values_list("username", flat=True)[:2]
    )
    return matches[0] if len(matches) == 1 else identifier


def _frontend_base(request):
    configured_base = getattr(settings, "FRONTEND_BASE_URL", "")
    if configured_base:
        return configured_base.rstrip("/")

    origin = request.META.get("HTTP_ORIGIN", "").rstrip("/")
    allowed = {
        origin.rstrip("/") for origin in getattr(settings, "CORS_ALLOWED_ORIGINS", [])
    }
    if origin and origin in allowed:
        return origin

    return request.build_absolute_uri("/").rstrip("/")


def _reset_link(request, token):
    return f"{_frontend_base(request)}/reset-password?token={token}"


def _password_reset_token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _password_reset_token_expiry():
    lifetime_minutes = getattr(settings, "PASSWORD_RESET_TOKEN_TTL_MINUTES", 60)
    return timezone.now() - timedelta(minutes=lifetime_minutes)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=_login_username_for_identifier(
                serializer.validated_data["username"]
            ),
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        profile = Profile.objects.filter(user=user).first()
        if profile and not profile.is_active:
            return Response(
                {"detail": "This portal account is disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )
        role = profile_role_for_user(user)
        if role is None:
            return Response(
                {"detail": "This account does not have an active portal role."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if maintenance_mode_enabled() and role != Profile.ROLE_ADMIN:
            return Response(
                {"detail": str(MaintenanceModeUnavailable.default_detail)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if role == Profile.ROLE_LIBRARIAN and (
            not feature_enabled("library")
            or not role_module_enabled(role, "library")
        ):
            return Response(
                {"detail": "Librarian access is currently disabled by library module settings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if role == Profile.ROLE_CATERER and (
            not feature_enabled("canteen")
            or not role_module_enabled(role, "canteen")
        ):
            return Response(
                {"detail": "Caterer access is currently disabled by dining module settings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = issue_ums_refresh(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if request.data.get("role") == Profile.ROLE_STUDENT:
            managed_hostel_room(request.data.get("room"), lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request, *args, **kwargs):
        _enforce_maintenance_access(request.user)
        return Response({"user": UserSerializer(request.user).data})

    def patch(self, request, *args, **kwargs):
        _enforce_maintenance_access(request.user)
        profile, _created = Profile.objects.get_or_create(user=request.user)
        previous_picture = profile.profile_picture
        serializer = ProfilePictureUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        if previous_picture and previous_picture.name != profile.profile_picture.name:
            previous_picture.delete(save=False)

        request.user._state.fields_cache.pop("profile", None)
        return Response({"user": UserSerializer(request.user).data})


class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        reset_link = None
        email_sent = False
        email_reason = ""

        profiles = Profile.objects.select_related("user").filter(
            user__email__iexact=email,
            user__is_active=True,
            is_active=True,
        )
        for profile in profiles:
            user = profile.user
            token = secrets.token_urlsafe(32)
            configured_portal_name = portal_name()
            profile.password_reset_token = _password_reset_token_digest(token)
            profile.password_reset_requested_at = timezone.now()
            profile.save(
                update_fields=[
                    "password_reset_token",
                    "password_reset_requested_at",
                    "updated_at",
                ]
            )
            reset_link = _reset_link(request, token)
            display_name = user.get_full_name().strip() or user.username
            try:
                send_mail(
                    subject=f"Reset your {configured_portal_name} password",
                    message=(
                        f"Hi {display_name},\n\n"
                        f"Username: {user.username}\n\n"
                        "This is your password reset link. Click here to reset your password:\n"
                        f"{reset_link}\n\n"
                        f"This link expires in {settings.PASSWORD_RESET_TOKEN_TTL_MINUTES} minutes "
                        "and can only be used once.\n\n"
                        "If you did not request this, you can ignore this email."
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as error:
                logger.exception(
                    "Unable to send password reset email for user_id=%s.",
                    user.pk,
                )
                email_reason = str(error)

        payload = {
            "detail": "If an account exists for this email, a verification link has been sent."
        }
        if settings.DEBUG:
            payload["debug"] = {
                "email_sent": email_sent,
                "reason": email_reason or "Debug mode includes the reset link for local testing.",
            }
            if reset_link:
                payload["reset_link"] = reset_link

        return Response(payload, status=status.HTTP_200_OK)


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"].strip()
        password = serializer.validated_data["password"]

        profile = Profile.objects.filter(
            password_reset_token=_password_reset_token_digest(token),
        ).first()
        if not profile:
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            not profile.password_reset_requested_at
            or profile.password_reset_requested_at < _password_reset_token_expiry()
        ):
            profile.password_reset_token = None
            profile.password_reset_requested_at = None
            profile.save(
                update_fields=[
                    "password_reset_token",
                    "password_reset_requested_at",
                    "updated_at",
                ]
            )
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password, profile.user)
        except DjangoValidationError as error:
            return Response(
                {"detail": " ".join(error.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = profile.user
        user.set_password(password)
        user.save(update_fields=["password"])

        profile.password_reset_token = None
        profile.password_reset_requested_at = None
        profile.save(
            update_fields=[
                "password_reset_token",
                "password_reset_requested_at",
                "updated_at",
            ]
        )

        return Response(
            {"detail": "Password reset successful. You can now login with your new password."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsActiveUmsUser]

    def post(self, request, *args, **kwargs):
        _enforce_maintenance_access(request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": ["Current password is incorrect."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = serializer.validated_data["new_password"]
        try:
            validate_password(new_password, request.user)
        except DjangoValidationError as error:
            return Response(
                {"new_password": error.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        Profile.objects.filter(user=request.user).update(
            password_reset_token=None,
            password_reset_requested_at=None,
        )
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class SendEmailVerificationView(APIView):
    permission_classes = [IsActiveUmsUser]

    def post(self, request, *args, **kwargs):
        _enforce_maintenance_access(request.user)
        return Response(
            {
                "detail": "Email verification is not required for this portal account.",
                "is_email_verified": True,
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    permission_classes = [IsActiveUmsUser]

    def post(self, request, *args, **kwargs):
        _enforce_maintenance_access(request.user)
        return Response(
            {
                "detail": "Email verified.",
                "username": request.user.username,
                "is_email_verified": True,
            },
            status=status.HTTP_200_OK,
        )


class UmsTokenRefreshSerializer(TokenRefreshSerializer):
    default_error_messages = {
        **TokenRefreshSerializer.default_error_messages,
        "no_active_ums_role": "No active portal account found for the given token.",
    }

    def validate(self, attrs):
        try:
            refresh = self.token_class(attrs["refresh"])
        except User.DoesNotExist as error:
            raise AuthenticationFailed(
                self.error_messages["no_active_ums_role"],
                "no_active_ums_role",
            ) from error

        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        user = (
            User.objects.filter(
                **{api_settings.USER_ID_FIELD: user_id},
            ).first()
            if user_id is not None
            else None
        )
        role = profile_role_for_user(user)
        if role is None:
            raise AuthenticationFailed(
                self.error_messages["no_active_ums_role"],
                "no_active_ums_role",
            )
        if maintenance_mode_enabled() and role != Profile.ROLE_ADMIN:
            raise MaintenanceModeUnavailable()
        if role == Profile.ROLE_LIBRARIAN and (
            not feature_enabled("library")
            or not role_module_enabled(role, "library")
        ):
            raise AuthenticationFailed(
                "Librarian access is currently disabled by library module settings.",
                "feature_disabled",
            )
        if role == Profile.ROLE_CATERER and (
            not feature_enabled("canteen")
            or not role_module_enabled(role, "canteen")
        ):
            raise AuthenticationFailed(
                "Caterer access is currently disabled by dining module settings.",
                "feature_disabled",
            )

        seconds_remaining = session_seconds_remaining(refresh)
        access = cap_token_to_ums_session(refresh.access_token, seconds_remaining)
        data = {"access": str(access)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass
            rotate_refresh_with_ums_session(refresh, seconds_remaining)
            data["refresh"] = str(refresh)

        return data


class UmsTokenRefreshView(TokenRefreshView):
    serializer_class = UmsTokenRefreshSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token_refresh"


register = RegisterView
login = LoginView
forgot_password = ForgotPasswordView
reset_password = ResetPasswordView
change_password = ChangePasswordView
send_email_verification = SendEmailVerificationView
verify_email = VerifyEmailView
me = MeView
