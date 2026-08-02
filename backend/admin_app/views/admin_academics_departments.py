from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.serializers import CenterSerializer, DepartmentSerializer, SchoolSerializer
from core.common.errors import first_error as _first_error


class AdminAcademicsDepartments(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        departments = (
            models.Department.objects.select_related("school", "center")
            .all()
            .order_by("name")
        )
        return Response(
            {
                "title": "Academic Departments",
                "section": "admin",
                "departments": DepartmentSerializer(departments, many=True).data,
                "schools": SchoolSerializer(
                    models.School.objects.filter(is_active=True).order_by("name"),
                    many=True,
                ).data,
                "centers": CenterSerializer(
                    models.Center.objects.filter(is_active=True).order_by("name"),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        department = serializer.save()
        return Response(
            {
                "message": "Department created successfully.",
                "department": DepartmentSerializer(department).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminAcademicsDepartmentDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            department = models.Department.objects.get(pk=pk)
        except models.Department.DoesNotExist:
            return Response(
                {"detail": "Department not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        department = serializer.save()
        return Response(
            {
                "message": "Department updated successfully.",
                "department": DepartmentSerializer(department).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            department = models.Department.objects.get(pk=pk)
        except models.Department.DoesNotExist:
            return Response(
                {"detail": "Department not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        department.delete()
        return Response(
            {"message": "Department deleted successfully."},
            status=status.HTTP_200_OK,
        )
