from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from admin_app import models
from home_app.serializers import PublicCenterSerializer


class PublicCentres(APIView):
    def get(self, request):
        centres = (
            models.Center.objects.filter(is_active=True)
            .exclude(slug__isnull=True)
            .exclude(slug="")
            .order_by("name")
        )
        return Response(
            {
                "title": "Centres",
                "section": "public",
                "centres": PublicCenterSerializer(centres, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class PublicCentreDetail(APIView):
    def get(self, request, slug):
        try:
            centre = models.Center.objects.get(slug=slug, is_active=True)
        except models.Center.DoesNotExist:
            return Response(
                {"detail": "Centre not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "title": centre.name,
                "section": "public",
                "centre": PublicCenterSerializer(centre).data,
            },
            status=status.HTTP_200_OK,
        )
