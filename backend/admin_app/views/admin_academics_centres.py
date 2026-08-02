from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify

from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.serializers import CenterSerializer
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


class AdminAcademicsCentres(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        centres = models.Center.objects.all().order_by("name")
        return Response(
            {
                "title": "Academic Centres",
                "section": "admin",
                "centres": CenterSerializer(centres, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        payload = _normalize_slug(request.data.copy())
        if not payload.get("slug"):
            return Response(
                {"detail": "Slug is required for public centre pages."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CenterSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        centre = serializer.save()
        return Response(
            {
                "message": "Centre created successfully.",
                "centre": CenterSerializer(centre).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminAcademicsCentreDetail(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            centre = models.Center.objects.get(pk=pk)
        except models.Center.DoesNotExist:
            return Response(
                {"detail": "Centre not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = _normalize_slug(request.data.copy())
        if "slug" in payload and not payload.get("slug"):
            return Response(
                {"detail": "Slug is required for public centre pages."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CenterSerializer(centre, data=payload, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        centre = serializer.save()
        return Response(
            {
                "message": "Centre updated successfully.",
                "centre": CenterSerializer(centre).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            centre = models.Center.objects.get(pk=pk)
        except models.Center.DoesNotExist:
            return Response(
                {"detail": "Centre not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        centre.delete()
        return Response(
            {"message": "Centre deleted successfully."},
            status=status.HTTP_200_OK,
        )
