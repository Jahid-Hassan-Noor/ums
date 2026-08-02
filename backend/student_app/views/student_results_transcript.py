from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsStudentRole
from student_app.results_service import transcript_payload


class StudentResultsTranscript(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(transcript_payload(request), status=status.HTTP_200_OK)
