from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from admin_app import models
from home_app.serializers import PublicCenterSerializer, PublicDepartmentSerializer


class PublicDepartments(APIView):
    def get(self, request):
        departments = (
            models.Department.objects.select_related("school", "center")
            .filter(is_active=True)
            .order_by("name")
        )
        support_centres = (
            models.Center.objects.filter(is_active=True)
            .exclude(code__in=["ADMIN", "CDAE", "CFGS", "CGS", "LC"])
            .exclude(slug__isnull=True)
            .exclude(slug="")
            .order_by("name")
        )
        return Response(
            {
                "title": "Departments",
                "section": "public",
                "departments": PublicDepartmentSerializer(departments, many=True).data,
                "centres": PublicCenterSerializer(support_centres, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
