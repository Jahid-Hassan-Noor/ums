from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.setup_wizard import setup_wizard_payload
from auth_app.permissions import IsAdminRole


class AdminSetupWizard(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(setup_wizard_payload(), status=status.HTTP_200_OK)


__all__ = ["AdminSetupWizard"]
