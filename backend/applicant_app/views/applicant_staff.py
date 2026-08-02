from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsApplicantStaffRole
from applicant_app import models
from applicant_app.notifications import (
    notify_application_status_changed,
    notify_scholarship_status_changed,
)
from applicant_app.serializers import (
    AdmissionApplicationSerializer,
    ApplicationDocumentSerializer,
    ScholarshipApplicationSerializer,
    StaffApplicationStatusSerializer,
    StaffDocumentReviewSerializer,
    StaffScholarshipReviewSerializer,
)
from applicant_app.views.helpers import profile_for_user


def _interview_note(validated_data):
    if validated_data.get("status") != models.AdmissionApplication.STATUS_INTERVIEW:
        return ""
    lines = []
    if validated_data.get("interview_at"):
        lines.append(
            f"Interview schedule: {timezone.localtime(validated_data['interview_at']).strftime('%d %b %Y, %I:%M %p')}"
        )
    if validated_data.get("interview_location"):
        lines.append(f"Interview location: {validated_data['interview_location'].strip()}")
    if validated_data.get("interview_details"):
        lines.append(f"Interview details: {validated_data['interview_details'].strip()}")
    return "\n".join(lines)


class StaffApplicationCollectionView(APIView):
    permission_classes = [IsApplicantStaffRole]

    def get(self, request, *args, **kwargs):
        queryset = models.AdmissionApplication.objects.select_related(
            "applicant__profile__user",
            "intake",
        ).prefetch_related(
            "documents",
            "status_events",
        )
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response(AdmissionApplicationSerializer(queryset, many=True, context={"request": request}).data)


class StaffApplicationStatusView(APIView):
    permission_classes = [IsApplicantStaffRole]

    @transaction.atomic
    def patch(self, request, application_id, *args, **kwargs):
        serializer = StaffApplicationStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = get_object_or_404(
            models.AdmissionApplication.objects.select_related(
                "applicant__profile__user",
                "intake",
            ).prefetch_related(
                "documents",
                "status_events",
            ),
            id=application_id,
        )
        reviewer = profile_for_user(request.user)
        old_status = application.status
        application.status = serializer.validated_data["status"]
        note_parts = [
            serializer.validated_data.get("note", "").strip(),
            _interview_note(serializer.validated_data),
        ]
        status_note = "\n".join(part for part in note_parts if part).strip()
        application.review_notes = serializer.validated_data.get("review_notes", application.review_notes)
        if status_note and not application.review_notes:
            application.review_notes = status_note
        application.reviewed_by = reviewer
        application.save(update_fields=["status", "review_notes", "reviewed_by", "updated_at"])
        models.ApplicationStatusEvent.objects.create(
            application=application,
            from_status=old_status,
            to_status=application.status,
            note=status_note,
            created_by=reviewer,
        )
        notify_application_status_changed(application, reviewer)
        return Response(AdmissionApplicationSerializer(application, context={"request": request}).data)


class StaffScholarshipReviewView(APIView):
    permission_classes = [IsApplicantStaffRole]

    def patch(self, request, application_id, *args, **kwargs):
        serializer = StaffScholarshipReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = get_object_or_404(models.AdmissionApplication, id=application_id)
        scholarship, _ = models.ScholarshipApplication.objects.get_or_create(application=application)
        for key, value in serializer.validated_data.items():
            setattr(scholarship, key, value)
        scholarship.reviewed_by = profile_for_user(request.user)
        scholarship.reviewed_at = timezone.now()
        scholarship.save()
        notify_scholarship_status_changed(scholarship)
        return Response(ScholarshipApplicationSerializer(scholarship).data)


class StaffApplicationDocumentReviewView(APIView):
    permission_classes = [IsApplicantStaffRole]

    @transaction.atomic
    def patch(self, request, document_id, *args, **kwargs):
        serializer = StaffDocumentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = get_object_or_404(
            models.ApplicationDocument.objects.select_related(
                "application__applicant__profile__user",
            ),
            id=document_id,
        )
        document.status = serializer.validated_data["status"]
        document.notes = serializer.validated_data.get("notes", document.notes)
        document.reviewed_by = profile_for_user(request.user)
        document.reviewed_at = timezone.now()
        document.save(update_fields=["status", "notes", "reviewed_by", "reviewed_at"])
        return Response(ApplicationDocumentSerializer(document, context={"request": request}).data)


__all__ = [
    "StaffApplicationCollectionView",
    "StaffApplicationStatusView",
    "StaffApplicationDocumentReviewView",
    "StaffScholarshipReviewView",
]
