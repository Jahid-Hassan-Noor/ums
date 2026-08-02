from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole
from admin_app.views.public_content_utils import (
    first_error,
    profile_for_request,
    request_payload,
)
from home_app import models as public_models
from home_app.serializers import PublicAnnouncementSerializer


class AdminPublicAnnouncements(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        announcements = public_models.PublicAnnouncement.objects.all().order_by(
            "-is_pinned",
            "-starts_at",
            "-created_at",
        )
        return Response(
            {
                "title": "Public Announcements",
                "section": "admin",
                "announcements": PublicAnnouncementSerializer(
                    announcements,
                    many=True,
                ).data,
                "audiences": [
                    {"value": value, "label": label}
                    for value, label in public_models.PublicAnnouncement.AUDIENCE_CHOICES
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = PublicAnnouncementSerializer(data=request_payload(request))
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        announcement = serializer.save(published_by=profile_for_request(request))
        return Response(
            {
                "message": "Announcement created successfully.",
                "announcement": PublicAnnouncementSerializer(announcement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminPublicAnnouncementDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            announcement = public_models.PublicAnnouncement.objects.get(pk=pk)
        except public_models.PublicAnnouncement.DoesNotExist:
            return Response(
                {"detail": "Announcement not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PublicAnnouncementSerializer(
            announcement,
            data=request_payload(request),
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        announcement = serializer.save()
        return Response(
            {
                "message": "Announcement updated successfully.",
                "announcement": PublicAnnouncementSerializer(announcement).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            announcement = public_models.PublicAnnouncement.objects.get(pk=pk)
        except public_models.PublicAnnouncement.DoesNotExist:
            return Response(
                {"detail": "Announcement not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        announcement.delete()
        return Response(
            {"message": "Announcement deleted successfully."},
            status=status.HTTP_200_OK,
        )
