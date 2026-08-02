from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsExecutiveRole
from admin_app.serializers import CenterSerializer, ProgramSerializer, SchoolSerializer
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    scope_payload,
    scope_supports_academic_workflows,
)
from core.common.errors import first_error as _first_error


def _scope_or_response(user):
    profile = get_executive_profile(user)
    try:
        scope = get_executive_scope(profile)
    except ValueError as exc:
        return None, Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if not scope.get("kind"):
        return None, Response(
            {"detail": "Executive must be assigned to one school or centre."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return scope, None


def _unit_serializer(scope):
    if scope["kind"] == "school":
        return "school", SchoolSerializer(scope["unit"]).data
    return "centre", CenterSerializer(scope["unit"]).data


class ExecutiveOrganization(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        scope, error = _scope_or_response(request.user)
        if error:
            return error
        unit_label, unit_data = _unit_serializer(scope)
        return Response(
            {
                "title": "Organisation Details",
                "section": "executive",
                "scope": scope_payload(scope),
                "unit_label": unit_label,
                "unit": unit_data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        scope, error = _scope_or_response(request.user)
        if error:
            return error

        allowed_fields = {
            "name",
            "description",
            "about",
            "vision",
            "mission",
            "programmes",
            "offerings",
            "image_url",
            "is_active",
        }
        payload = {
            field: value
            for field, value in request.data.items()
            if field in allowed_fields
        }

        serializer_class = SchoolSerializer if scope["kind"] == "school" else CenterSerializer
        serializer = serializer_class(scope["unit"], data=payload, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        unit = serializer.save()
        return Response(
            {
                "message": "Organisation details updated successfully.",
                "unit": serializer_class(unit).data,
                "scope": scope_payload({"kind": scope["kind"], "unit": unit}),
            },
            status=status.HTTP_200_OK,
        )


class ExecutivePrograms(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        scope, error = _scope_or_response(request.user)
        if error:
            return error

        programmes = (
            models.Program.objects.select_related("school", "center", "department")
            .filter(**{scope["kind"]: scope["unit"]})
            .order_by("name")
        )
        return Response(
            {
                "title": "Programmes",
                "section": "executive",
                "scope": scope_payload(scope),
                "program_types": [
                    {"value": value, "label": label}
                    for value, label in models.Program.PROGRAM_CHOICES
                ],
                "programmes": ProgramSerializer(programmes, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        scope, error = _scope_or_response(request.user)
        if error:
            return error

        payload = request.data.copy()
        if scope["kind"] == "school":
            payload["school"] = scope["unit"].id
            payload["center"] = None
            payload["program_type"] = models.Program.PROGRAM_ACADEMIC
        else:
            payload["center"] = scope["unit"].id
            payload["school"] = None
            if not scope_supports_academic_workflows(scope):
                payload["program_type"] = models.Program.PROGRAM_CENTER
            else:
                payload["program_type"] = payload.get("program_type") or models.Program.PROGRAM_ACADEMIC

        serializer = ProgramSerializer(data=payload)
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

    def patch(self, request):
        scope, error = _scope_or_response(request.user)
        if error:
            return error

        programme_id = request.query_params.get("programme_id")
        programme = (
            models.Program.objects.filter(pk=programme_id, **{scope["kind"]: scope["unit"]})
            .first()
        )
        if not programme:
            return Response(
                {"detail": "Programme not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = request.data.copy()
        payload.pop("school", None)
        payload.pop("center", None)
        if scope["kind"] == "school":
            payload["program_type"] = models.Program.PROGRAM_ACADEMIC
        elif not scope_supports_academic_workflows(scope):
            payload["program_type"] = models.Program.PROGRAM_CENTER

        serializer = ProgramSerializer(programme, data=payload, partial=True)
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

    def delete(self, request):
        scope, error = _scope_or_response(request.user)
        if error:
            return error

        programme_id = request.query_params.get("programme_id")
        programme = (
            models.Program.objects.filter(pk=programme_id, **{scope["kind"]: scope["unit"]})
            .first()
        )
        if not programme:
            return Response(
                {"detail": "Programme not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        programme.is_active = False
        programme.save(update_fields=["is_active"])
        return Response(
            {"message": "Programme archived successfully."},
            status=status.HTTP_200_OK,
        )
