from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole
from admin_app.views.public_content_utils import (
    first_error,
    normalize_slug,
    profile_for_request,
    publish_now_if_needed,
    request_payload,
)
from home_app import models as public_models
from home_app.serializers import PublicNewsSerializer


class AdminPublicNews(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        news = public_models.PublicNews.objects.all().order_by(
            "-published_at",
            "-created_at",
        )
        return Response(
            {
                "title": "Public News",
                "section": "admin",
                "news": PublicNewsSerializer(
                    news,
                    many=True,
                    context={"request": request},
                ).data,
                "statuses": [
                    {"value": value, "label": label}
                    for value, label in public_models.PublicNews.STATUS_CHOICES
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        payload = publish_now_if_needed(normalize_slug(request_payload(request)))
        serializer = PublicNewsSerializer(data=payload, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        news = serializer.save(author=profile_for_request(request))
        return Response(
            {
                "message": "News item created successfully.",
                "news": PublicNewsSerializer(news, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminPublicNewsDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            news = public_models.PublicNews.objects.get(pk=pk)
        except public_models.PublicNews.DoesNotExist:
            return Response(
                {"detail": "News item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = publish_now_if_needed(normalize_slug(request_payload(request)))
        serializer = PublicNewsSerializer(
            news,
            data=payload,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        news = serializer.save()
        return Response(
            {
                "message": "News item updated successfully.",
                "news": PublicNewsSerializer(news, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            news = public_models.PublicNews.objects.get(pk=pk)
        except public_models.PublicNews.DoesNotExist:
            return Response(
                {"detail": "News item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        news.delete()
        return Response(
            {"message": "News item deleted successfully."},
            status=status.HTTP_200_OK,
        )
