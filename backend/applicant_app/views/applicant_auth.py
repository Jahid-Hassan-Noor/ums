from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsApplicantRole
from admin_app.settings_registry import maintenance_mode_enabled, setting_value
from applicant_app.serializers import (
    ApplicantLoginSerializer,
    ApplicantRegisterSerializer,
    ApplicantSerializer,
    ApplicantUpdateSerializer,
)
from applicant_app.views.helpers import applicant_for_user, auth_payload


User = get_user_model()


class ApplicantRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not setting_value("security", "applicant_registration_enabled"):
            return Response(
                {"detail": "Applicant self-registration is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = ApplicantRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        applicant = serializer.save()
        return Response(auth_payload(applicant.user), status=status.HTTP_201_CREATED)


class ApplicantLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if maintenance_mode_enabled():
            return Response(
                {"detail": "The UMS is currently in maintenance mode."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = ApplicantLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get("username", "").strip()
        email = serializer.validated_data.get("email", "").strip().lower()
        if not username and email:
            username = (
                User.objects.filter(email__iexact=email)
                .values_list("username", flat=True)
                .first()
                or email
            )
        user = authenticate(
            request,
            username=username,
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        applicant = applicant_for_user(user)
        if not applicant:
            return Response(
                {"detail": "This account is not registered as an applicant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(auth_payload(user), status=status.HTTP_200_OK)


class ApplicantMeView(APIView):
    permission_classes = [IsApplicantRole]

    def get(self, request, *args, **kwargs):
        applicant = applicant_for_user(request.user)
        if not applicant:
            return Response(
                {"detail": "Applicant profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"applicant": ApplicantSerializer(applicant).data})

    def patch(self, request, *args, **kwargs):
        applicant = applicant_for_user(request.user)
        if not applicant:
            return Response(
                {"detail": "Applicant profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        immutable_errors = {}
        if "email" in request.data and request.data.get("email") != request.user.email:
            immutable_errors["email"] = "Email address cannot be changed."
        if "username" in request.data and request.data.get("username") != request.user.username:
            immutable_errors["username"] = "Username cannot be changed."
        if immutable_errors:
            return Response(immutable_errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApplicantUpdateSerializer(applicant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        applicant = serializer.save()
        return Response({"applicant": ApplicantSerializer(applicant).data})


__all__ = ["ApplicantLoginView", "ApplicantMeView", "ApplicantRegisterView"]
