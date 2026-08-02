from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsApplicantRole
from applicant_app import models
from applicant_app.notifications import notify_application_submitted
from applicant_app.serializers import (
    AdmissionApplicationSerializer,
    ApplicationSubmitSerializer,
)
from applicant_app.views.helpers import applicant_for_user, required_submission_gaps


class ApplicationCollectionView(APIView):
    permission_classes = [IsApplicantRole]

    def get(self, request, *args, **kwargs):
        applicant = applicant_for_user(request.user)
        if not applicant:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        queryset = applicant.applications.select_related(
            "intake",
            "applicant__profile__user",
        ).prefetch_related(
            "documents",
            "status_events",
        )
        return Response(AdmissionApplicationSerializer(queryset, many=True, context={"request": request}).data)

    def post(self, request, *args, **kwargs):
        applicant = applicant_for_user(request.user)
        if not applicant:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdmissionApplicationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        application = serializer.save(applicant=applicant)
        models.ApplicationStatusEvent.objects.create(
            application=application,
            to_status=application.status,
            note="Application draft created.",
        )
        return Response(
            AdmissionApplicationSerializer(application, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ApplicationDetailView(APIView):
    permission_classes = [IsApplicantRole]

    def get_application(self, request, application_id):
        applicant = applicant_for_user(request.user)
        if not applicant:
            return None
        return get_object_or_404(
            models.AdmissionApplication.objects.select_related(
                "intake",
                "applicant__profile__user",
            ).prefetch_related(
                "documents",
                "status_events",
            ),
            id=application_id,
            applicant=applicant,
        )

    def get(self, request, application_id, *args, **kwargs):
        application = self.get_application(request, application_id)
        if application is None:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdmissionApplicationSerializer(application, context={"request": request}).data)

    def patch(self, request, application_id, *args, **kwargs):
        application = self.get_application(request, application_id)
        if application is None:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        if application.status not in {
            models.AdmissionApplication.STATUS_DRAFT,
            models.AdmissionApplication.STATUS_INFO_REQUESTED,
        }:
            return Response(
                {"detail": "Submitted applications cannot be edited unless information is requested."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AdmissionApplicationSerializer(
            application,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(AdmissionApplicationSerializer(application, context={"request": request}).data)


class ApplicationSubmitView(APIView):
    permission_classes = [IsApplicantRole]

    @transaction.atomic
    def post(self, request, application_id, *args, **kwargs):
        serializer = ApplicationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        applicant = applicant_for_user(request.user)
        if not applicant:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        application = get_object_or_404(models.AdmissionApplication, id=application_id, applicant=applicant)
        if application.status not in {
            models.AdmissionApplication.STATUS_DRAFT,
            models.AdmissionApplication.STATUS_INFO_REQUESTED,
        }:
            return Response({"detail": "This application has already been submitted."}, status=status.HTTP_400_BAD_REQUEST)

        gaps = required_submission_gaps(application)
        if gaps:
            return Response(
                {"detail": "Application is incomplete.", "missing": gaps},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = application.status
        application.status = models.AdmissionApplication.STATUS_SUBMITTED
        application.current_step = models.AdmissionApplication.STEP_SUBMITTED
        application.submitted_at = timezone.now()
        application.save(update_fields=["status", "current_step", "submitted_at", "updated_at"])
        models.ApplicationStatusEvent.objects.create(
            application=application,
            from_status=old_status,
            to_status=application.status,
            note="Application submitted by applicant.",
        )
        if application.scholarship_requested:
            models.ScholarshipApplication.objects.get_or_create(
                application=application,
                defaults={
                    "status": models.ScholarshipApplication.STATUS_SUBMITTED,
                    "personal_statement": (application.scholarship_information or {}).get("personal_statement", ""),
                    "household_income": (application.scholarship_information or {}).get("household_income") or None,
                    "dependents_count": (application.scholarship_information or {}).get("dependents_count") or 0,
                    "financial_need_notes": (application.scholarship_information or {}).get("financial_need_notes", ""),
                },
            )
        notify_application_submitted(application)
        return Response(AdmissionApplicationSerializer(application, context={"request": request}).data)


__all__ = ["ApplicationCollectionView", "ApplicationDetailView", "ApplicationSubmitView"]
