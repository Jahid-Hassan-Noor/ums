from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.audit import audit_log_response
from admin_app.models import AuditLog, Profile
from auth_app.permissions import IsExecutiveRole
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    scope_payload,
)


class ExecutiveAuditLog(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not scope.get("kind") or not scope.get("unit"):
            return Response(
                {"detail": "Executive must be assigned to one school or centre."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = AuditLog.objects.filter(
            user__role=Profile.ROLE_EXECUTIVE,
            details__scope__kind=scope["kind"],
            details__scope__id=scope["unit"].id,
        )
        return audit_log_response(
            request,
            queryset=queryset,
            extra={
                "title": "Executive Audit Log",
                "section": "executive",
                "scope": scope_payload(scope),
            },
        )
