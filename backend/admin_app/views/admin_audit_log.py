from rest_framework.views import APIView

from admin_app.audit import audit_log_response
from auth_app.permissions import IsAdminRole


class AdminAuditLog(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return audit_log_response(
            request,
            extra={"title": "Audit Log", "section": "admin"},
        )
