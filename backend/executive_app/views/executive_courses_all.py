from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsExecutiveRole
from admin_app.serializers import CourseSerializer
from executive_app.course_prerequisites import prerequisite_options, resolve_prerequisites
from executive_app.course_schedule import (
    courses_for_scope,
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    parse_positive_int,
    scope_payload,
    scope_supports_academic_workflows,
)


def _course_payload(request, include_inactive=True):
    profile = get_executive_profile(request.user)
    try:
        scope = get_executive_scope(profile)
        scope_error = None
    except ValueError as exc:
        scope = {"kind": None, "unit": None}
        scope_error = str(exc)
    if scope.get("kind") and not scope_supports_academic_workflows(scope):
        return {
            "title": "All Courses",
            "section": "executive",
            "scope": scope_payload(scope),
            "scope_error": non_academic_scope_response(scope)["detail"],
            "courses": [],
            "prerequisite_options": [],
        }

    courses = courses_for_scope(scope)
    if not include_inactive:
        courses = courses.filter(is_active=True)

    return {
        "title": "All Courses",
        "section": "executive",
        "scope": scope_payload(scope),
        "scope_error": scope_error,
        "courses": CourseSerializer(courses, many=True).data,
        "prerequisite_options": CourseSerializer(
            prerequisite_options(scope),
            many=True,
        ).data
        if not scope_error
        else [],
    }


class ExecutiveCoursesAll(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        return Response(_course_payload(request), status=status.HTTP_200_OK)

    def patch(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        course_id = request.query_params.get("course_id")
        course = courses_for_scope(scope).filter(pk=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        code = str(data.get("code", course.code)).strip().upper()
        title = str(data.get("title", course.title)).strip()
        credits = parse_positive_int(data.get("credits"), default=course.credits)
        description = str(data.get("description", course.description)).strip()
        has_lab = bool(data.get("has_lab", course.has_lab))
        prerequisites, prerequisite_error = resolve_prerequisites(
            scope,
            data.get("prerequisites", list(course.prerequisites.values_list("id", flat=True))),
            course=course,
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

        duplicate = models.Course.objects.exclude(pk=course.pk).filter(code=code).exists()
        if duplicate:
            return Response(
                {"detail": "Another course already uses this course code."},
                status=status.HTTP_409_CONFLICT,
            )

        course.code = code
        course.title = title
        course.credits = credits
        course.description = description
        course.has_lab = has_lab
        if "is_active" in data:
            course.is_active = bool(data.get("is_active"))
        course.save(update_fields=["code", "title", "credits", "description", "has_lab", "is_active"])
        course.prerequisites.set(prerequisites)

        return Response(
            {
                "message": "Course updated successfully.",
                "course": CourseSerializer(course).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        course_id = request.query_params.get("course_id")
        course = courses_for_scope(scope).filter(pk=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        course.is_active = False
        course.save(update_fields=["is_active"])
        return Response({"message": "Course archived successfully."}, status=status.HTTP_200_OK)
