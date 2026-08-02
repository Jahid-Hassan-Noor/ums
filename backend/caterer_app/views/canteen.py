from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsCatererRole
from caterer_app.service import (
    account_payload,
    dashboard_summary,
    deduct,
    ensure_account,
    find_student,
)


def validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)


class CatererUms(APIView):
    permission_classes = [IsCatererRole]

    def get(self, request):
        return Response({"title": "Caterer Portal", "section": "caterer"})


class CatererDashboard(APIView):
    permission_classes = [IsCatererRole]

    def get(self, request):
        return Response(
            {
                "title": "Caterer Dashboard",
                "section": "caterer",
                "summary": dashboard_summary(),
            }
        )


class CatererStudentAccount(APIView):
    permission_classes = [IsCatererRole]

    def get(self, request):
        student = find_student(request.query_params.get("student_id"))
        if not student:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            account = ensure_account(student)
        except ValidationError as error:
            return validation_response(error)
        return Response({"account": account_payload(account)})


class CatererTransactions(APIView):
    permission_classes = [IsCatererRole]

    def post(self, request):
        student = find_student(request.data.get("student_id"))
        if not student:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            account, _transaction = deduct(
                student=student,
                caterer=request.user.profile,
                amount=request.data.get("amount"),
                description=request.data.get("description"),
            )
        except ValidationError as error:
            return validation_response(error)
        return Response(
            {
                "message": "Canteen transaction completed successfully.",
                "account": account_payload(account),
            },
            status=status.HTTP_201_CREATED,
        )


__all__ = [
    "CatererDashboard",
    "CatererUms",
    "CatererStudentAccount",
    "CatererTransactions",
]

