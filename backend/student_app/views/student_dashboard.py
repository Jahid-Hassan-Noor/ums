from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from auth_app.permissions import IsStudentRole
from caterer_app.service import (
    account_payload,
    canteen_module_enabled,
    module_unavailable_message,
    ensure_account,
)


class StudentDashboard(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        if not canteen_module_enabled():
            canteen_account = None
            canteen_message = module_unavailable_message()
        else:
            try:
                canteen_account = account_payload(ensure_account(request.user.profile))
                canteen_message = ""
            except ValidationError as error:
                canteen_account = None
                canteen_message = "; ".join(error.messages)
        return Response(
            {
                "title": "Dashboard",
                "section": "student",
                "canteen_account": canteen_account,
                "canteen_message": canteen_message,
            },
            status=status.HTTP_200_OK,
        )
