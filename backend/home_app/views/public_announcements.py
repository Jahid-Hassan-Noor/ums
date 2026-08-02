from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from home_app.serializers import PublicAnnouncementSerializer
from home_app.views.public_helpers import public_announcements, public_page_payload


class PublicAnnouncements(APIView):
    def get(self, request):
        payload = public_page_payload(
            request,
            "/announcements",
            "Announcements",
            "public",
        )
        payload.update(
            {
                "announcements": PublicAnnouncementSerializer(
                    public_announcements(),
                    many=True,
                ).data,
            }
        )
        return Response(payload, status=status.HTTP_200_OK)
