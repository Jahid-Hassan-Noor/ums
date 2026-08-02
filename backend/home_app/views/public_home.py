from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from home_app.serializers import (
    OfficialLinkSerializer,
    PublicAnnouncementSerializer,
    PublicEventSerializer,
    PublicNewsSerializer,
)
from home_app.views.public_helpers import (
    public_announcements,
    public_official_links,
    public_page_payload,
    published_events,
    published_news,
)


class PublicHome(APIView):
    def get(self, request):
        payload = public_page_payload(request, "/", "Home", "public")
        payload.update(
            {
                "news": PublicNewsSerializer(
                    published_news()[:6],
                    many=True,
                    context={"request": request},
                ).data,
                "events": PublicEventSerializer(
                    published_events()[:6],
                    many=True,
                ).data,
                "announcements": PublicAnnouncementSerializer(
                    public_announcements()[:4],
                    many=True,
                ).data,
                "official_links": OfficialLinkSerializer(
                    public_official_links()[:8],
                    many=True,
                ).data,
            }
        )
        return Response(payload, status=status.HTTP_200_OK)
