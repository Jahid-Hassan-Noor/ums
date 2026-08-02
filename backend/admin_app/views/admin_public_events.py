from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole
from admin_app.views.public_content_utils import (
    first_error,
    normalize_slug,
    profile_for_request,
    request_payload,
)
from home_app import models as public_models
from home_app.serializers import PublicEventSerializer


class AdminPublicEvents(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        events = public_models.PublicEvent.objects.all().order_by(
            "-starts_at",
            "title",
        )
        return Response(
            {
                "title": "Public Events",
                "section": "admin",
                "events": PublicEventSerializer(events, many=True).data,
                "statuses": [
                    {"value": value, "label": label}
                    for value, label in public_models.PublicEvent.STATUS_CHOICES
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        payload = normalize_slug(request_payload(request))
        serializer = PublicEventSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event = serializer.save(published_by=profile_for_request(request))
        return Response(
            {
                "message": "Event created successfully.",
                "event": PublicEventSerializer(event).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminPublicEventDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            event = public_models.PublicEvent.objects.get(pk=pk)
        except public_models.PublicEvent.DoesNotExist:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = normalize_slug(request_payload(request))
        serializer = PublicEventSerializer(event, data=payload, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event = serializer.save()
        return Response(
            {
                "message": "Event updated successfully.",
                "event": PublicEventSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            event = public_models.PublicEvent.objects.get(pk=pk)
        except public_models.PublicEvent.DoesNotExist:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        event.delete()
        return Response(
            {"message": "Event deleted successfully."},
            status=status.HTTP_200_OK,
        )
