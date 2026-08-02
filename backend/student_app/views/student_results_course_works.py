from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.results_service import courseworks_payload


class StudentResultsCourseWorks(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(courseworks_payload(request), status=status.HTTP_200_OK)
