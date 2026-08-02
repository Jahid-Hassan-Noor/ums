from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from admin_app import models
from home_app.serializers import PublicUnitSerializer


class PublicUnits(APIView):
    def get(self, request):
        units = (
            models.Unit.objects.select_related("school", "center", "department")
            .filter(is_active=True)
            .order_by("name")
        )
        return Response(
            {
                "title": "Units",
                "section": "public",
                "units": PublicUnitSerializer(units, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
