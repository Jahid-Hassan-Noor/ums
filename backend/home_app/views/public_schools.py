from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from admin_app import models
from home_app.serializers import PublicSchoolSerializer


class PublicSchools(APIView):
    def get(self, request):
        schools = (
            models.School.objects.filter(is_active=True)
            .exclude(slug__isnull=True)
            .exclude(slug="")
            .order_by("name")
        )
        return Response(
            {
                "title": "Schools",
                "section": "public",
                "schools": PublicSchoolSerializer(schools, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class PublicSchoolDetail(APIView):
    def get(self, request, slug):
        try:
            school = models.School.objects.get(slug=slug, is_active=True)
        except models.School.DoesNotExist:
            return Response(
                {"detail": "School not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "title": school.name,
                "section": "public",
                "school": PublicSchoolSerializer(school).data,
            },
            status=status.HTTP_200_OK,
        )
