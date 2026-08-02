from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.serializers import (
    CenterSerializer,
    DepartmentSerializer,
    SchoolSerializer,
    UnitSerializer,
)
from core.common.errors import first_error as _first_error


class AdminAcademicsUnits(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        units = (
            models.Unit.objects.select_related("school", "center", "department")
            .all()
            .order_by("name")
        )
        return Response(
            {
                "title": "Administrative Units",
                "section": "admin",
                "units": UnitSerializer(units, many=True).data,
                "unit_types": [
                    {"value": value, "label": label}
                    for value, label in models.Unit.UNIT_CHOICES
                ],
                "schools": SchoolSerializer(
                    models.School.objects.filter(is_active=True).order_by("name"),
                    many=True,
                ).data,
                "centers": CenterSerializer(
                    models.Center.objects.filter(is_active=True).order_by("name"),
                    many=True,
                ).data,
                "departments": DepartmentSerializer(
                    models.Department.objects.filter(is_active=True).order_by("name"),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = UnitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        unit = serializer.save()
        return Response(
            {
                "message": "Unit created successfully.",
                "unit": UnitSerializer(unit).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminAcademicsUnitDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            unit = models.Unit.objects.get(pk=pk)
        except models.Unit.DoesNotExist:
            return Response(
                {"detail": "Unit not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UnitSerializer(unit, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        unit = serializer.save()
        return Response(
            {
                "message": "Unit updated successfully.",
                "unit": UnitSerializer(unit).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            unit = models.Unit.objects.get(pk=pk)
        except models.Unit.DoesNotExist:
            return Response(
                {"detail": "Unit not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        unit.delete()
        return Response(
            {"message": "Unit deleted successfully."},
            status=status.HTTP_200_OK,
        )
