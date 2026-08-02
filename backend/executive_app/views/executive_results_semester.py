from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsExecutiveRole
from executive_app.results_service import executive_results_payload


class ExecutiveResultsSemester(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        return Response(
            executive_results_payload(request.user, view="semester"),
            status=status.HTTP_200_OK,
        )
