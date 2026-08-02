from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsExecutiveRole
from admin_app.serializers import CourseSerializer
from executive_app.course_prerequisites import prerequisite_options, resolve_prerequisites
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    parse_positive_int,
    scope_payload,
    scope_supports_academic_workflows,
)


class ExecutiveCoursesAdd(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
            scope_error = None
        except ValueError as exc:
            scope = {"kind": None, "unit": None}
            scope_error = str(exc)
        if scope.get("kind") and not scope_supports_academic_workflows(scope):
            scope_error = non_academic_scope_response(scope)["detail"]

        return Response(
            {
                "title": "Add Course",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
                "prerequisite_options": CourseSerializer(
                    prerequisite_options(scope),
                    many=True,
                ).data
                if not scope_error
                else [],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope.get("kind"):
            return Response(
                {"detail": "Executive must be assigned to one school or centre before adding courses."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        code = str(request.data.get("code", "")).strip().upper()
        title = str(request.data.get("title", "")).strip()
        description = str(request.data.get("description", "")).strip()
        credits = parse_positive_int(request.data.get("credits"))
        has_lab = bool(request.data.get("has_lab", False))
        prerequisites, prerequisite_error = resolve_prerequisites(
            scope,
            request.data.get("prerequisites", []),
        )

        if not code or not title:
            return Response(
                {"detail": "Course code and title are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if credits is None:
            return Response(
                {"detail": "Credits must be a positive number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if prerequisite_error:
            return Response({"detail": prerequisite_error}, status=status.HTTP_400_BAD_REQUEST)

        course = models.Course(
            code=code,
            title=title,
            description=description,
            credits=credits,
            has_lab=has_lab,
            is_active=True,
        )
        if scope["kind"] == "school":
            course.school = scope["unit"]
        if scope["kind"] == "center":
            course.center = scope["unit"]

        try:
            course.save()
            course.prerequisites.set(prerequisites)
        except IntegrityError:
            return Response(
                {"detail": "A course with this code already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "message": "Course added successfully.",
                "course": CourseSerializer(course).data,
            },
            status=status.HTTP_201_CREATED,
        )
