from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.serializers import (
    CenterSerializer,
    DepartmentSerializer,
    ProgramSerializer,
    SchoolSerializer,
)
from core.common.errors import first_error as _first_error


class AdminAcademicsProgrammes(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        programmes = (
            models.Program.objects.select_related("school", "center", "department")
            .all()
            .order_by("name")
        )
        return Response(
            {
                "title": "Academic Programmes",
                "section": "admin",
                "programmes": ProgramSerializer(programmes, many=True).data,
                "program_types": [
                    {"value": value, "label": label}
                    for value, label in models.Program.PROGRAM_CHOICES
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
        serializer = ProgramSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        programme = serializer.save()
        return Response(
            {
                "message": "Programme created successfully.",
                "programme": ProgramSerializer(programme).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminAcademicsProgrammeDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            programme = models.Program.objects.get(pk=pk)
        except models.Program.DoesNotExist:
            return Response(
                {"detail": "Programme not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProgramSerializer(programme, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        programme = serializer.save()
        return Response(
            {
                "message": "Programme updated successfully.",
                "programme": ProgramSerializer(programme).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            programme = models.Program.objects.get(pk=pk)
        except models.Program.DoesNotExist:
            return Response(
                {"detail": "Programme not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        programme.delete()
        return Response(
            {"message": "Programme deleted successfully."},
            status=status.HTTP_200_OK,
        )
