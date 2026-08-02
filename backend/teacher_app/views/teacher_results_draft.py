from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole
from executive_app.results_service import teacher_results_payload


class TeacherResultsDraft(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        return Response(
            teacher_results_payload(request.user, view="draft"),
            status=status.HTTP_200_OK,
        )
