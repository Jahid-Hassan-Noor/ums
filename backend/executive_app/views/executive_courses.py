from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsExecutiveRole
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    scope_payload,
    scope_supports_academic_workflows,
)


class ExecutiveCourses(APIView):
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
                "title": "Courses",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
            },
            status=status.HTTP_200_OK,
        )
