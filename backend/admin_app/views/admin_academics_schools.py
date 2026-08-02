from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify

from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.serializers import SchoolSerializer
from core.common.errors import first_error as _first_error




def _normalize_slug(payload):
    slug = str(payload.get("slug", "") or "").strip()
    if slug:
        payload["slug"] = slug
        return payload
    name = str(payload.get("name", "") or "").strip()
    if name:
        payload["slug"] = slugify(name)
    return payload


class AdminAcademicsSchools(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        schools = models.School.objects.all().order_by("name")
        return Response(
            {
                "title": "Academic Schools",
                "section": "admin",
                "schools": SchoolSerializer(schools, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        payload = _normalize_slug(request.data.copy())
        if not payload.get("slug"):
            return Response(
                {"detail": "Slug is required for public school pages."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SchoolSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        school = serializer.save()
        return Response(
            {
                "message": "School created successfully.",
                "school": SchoolSerializer(school).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminAcademicsSchoolDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            school = models.School.objects.get(pk=pk)
        except models.School.DoesNotExist:
            return Response(
                {"detail": "School not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = _normalize_slug(request.data.copy())
        if "slug" in payload and not payload.get("slug"):
            return Response(
                {"detail": "Slug is required for public school pages."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SchoolSerializer(school, data=payload, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        school = serializer.save()
        return Response(
            {
                "message": "School updated successfully.",
                "school": SchoolSerializer(school).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            school = models.School.objects.get(pk=pk)
        except models.School.DoesNotExist:
            return Response(
                {"detail": "School not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        school.delete()
        return Response(
            {"message": "School deleted successfully."},
            status=status.HTTP_200_OK,
        )
