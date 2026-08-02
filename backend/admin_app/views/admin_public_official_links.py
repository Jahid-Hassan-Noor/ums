from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole
from admin_app.views.public_content_utils import first_error, request_payload
from home_app import models as public_models
from home_app.serializers import OfficialLinkSerializer


class AdminPublicOfficialLinks(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        links = public_models.OfficialLink.objects.all().order_by(
            "category",
            "sort_order",
            "title",
        )
        return Response(
            {
                "title": "Official Links",
                "section": "admin",
                "official_links": OfficialLinkSerializer(links, many=True).data,
                "audiences": [
                    {"value": value, "label": label}
                    for value, label in public_models.OfficialLink.AUDIENCE_CHOICES
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = OfficialLinkSerializer(data=request_payload(request))
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        link = serializer.save()
        return Response(
            {
                "message": "Official link created successfully.",
                "official_link": OfficialLinkSerializer(link).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminPublicOfficialLinkDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            link = public_models.OfficialLink.objects.get(pk=pk)
        except public_models.OfficialLink.DoesNotExist:
            return Response(
                {"detail": "Official link not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OfficialLinkSerializer(link, data=request_payload(request), partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        link = serializer.save()
        return Response(
            {
                "message": "Official link updated successfully.",
                "official_link": OfficialLinkSerializer(link).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            link = public_models.OfficialLink.objects.get(pk=pk)
        except public_models.OfficialLink.DoesNotExist:
            return Response(
                {"detail": "Official link not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        link.delete()
        return Response(
            {"message": "Official link deleted successfully."},
            status=status.HTTP_200_OK,
        )
