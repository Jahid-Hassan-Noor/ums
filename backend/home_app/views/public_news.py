from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from home_app.serializers import PublicAnnouncementSerializer, PublicNewsSerializer
from home_app.views.public_helpers import (
    public_announcements,
    public_page_payload,
    published_news,
)


class PublicNews(APIView):
    def get(self, request):
        payload = public_page_payload(request, "/news", "News", "public")
        payload.update(
            {
                "news": PublicNewsSerializer(
                    published_news(),
                    many=True,
                    context={"request": request},
                ).data,
                "announcements": PublicAnnouncementSerializer(
                    public_announcements(),
                    many=True,
                ).data,
            }
        )
        return Response(payload, status=status.HTTP_200_OK)


class PublicNewsDetail(APIView):
    def get(self, request, slug):
        news = published_news().filter(slug=slug).first()
        if not news:
            return Response(
                {"detail": "News item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "title": news.title,
                "section": "public",
                "news": PublicNewsSerializer(news, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )
