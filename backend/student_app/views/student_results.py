from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsStudentRole
from student_app.results_service import semester_results_payload


class StudentResults(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(semester_results_payload(request), status=status.HTTP_200_OK)
