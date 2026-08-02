from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from home_app.serializers import PublicEventSerializer
from home_app.views.public_helpers import public_page_payload, published_events


class PublicEvents(APIView):
    def get(self, request):
        payload = public_page_payload(request, "/events", "Events", "public")
        payload.update(
            {
                "events": PublicEventSerializer(
                    published_events(),
                    many=True,
                ).data,
            }
        )
        return Response(payload, status=status.HTTP_200_OK)


class PublicEventDetail(APIView):
    def get(self, request, slug):
        event = published_events().filter(slug=slug).first()
        if not event:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "title": event.title,
                "section": "public",
                "event": PublicEventSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )
