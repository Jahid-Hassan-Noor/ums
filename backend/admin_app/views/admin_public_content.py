from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole
from admin_app.views.public_content_utils import (
    first_error,
    normalize_route_path,
    normalize_slug,
    publish_now_if_needed,
    request_payload,
)
from home_app import models as public_models
from home_app.serializers import PublicPageSerializer


class AdminPublicContent(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        pages = public_models.PublicPage.objects.all().order_by(
            "section",
            "sort_order",
            "title",
        )
        return Response(
            {
                "title": "Public Content",
                "section": "admin",
                "pages": PublicPageSerializer(pages, many=True).data,
                "sections": [
                    {"value": value, "label": label}
                    for value, label in public_models.PublicPage.SECTION_CHOICES
                ],
                "statuses": [
                    {"value": value, "label": label}
                    for value, label in public_models.PublicPage.STATUS_CHOICES
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        payload = publish_now_if_needed(
            normalize_route_path(normalize_slug(request_payload(request), 120))
        )
        serializer = PublicPageSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        page = serializer.save()
        return Response(
            {
                "message": "Public page created successfully.",
                "page": PublicPageSerializer(page).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminPublicContentDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            page = public_models.PublicPage.objects.get(pk=pk)
        except public_models.PublicPage.DoesNotExist:
            return Response(
                {"detail": "Public page not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = publish_now_if_needed(
            normalize_route_path(normalize_slug(request_payload(request), 120))
        )
        serializer = PublicPageSerializer(page, data=payload, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        page = serializer.save()
        return Response(
            {
                "message": "Public page updated successfully.",
                "page": PublicPageSerializer(page).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            page = public_models.PublicPage.objects.get(pk=pk)
        except public_models.PublicPage.DoesNotExist:
            return Response(
                {"detail": "Public page not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        page.delete()
        return Response(
            {"message": "Public page deleted successfully."},
            status=status.HTTP_200_OK,
        )
