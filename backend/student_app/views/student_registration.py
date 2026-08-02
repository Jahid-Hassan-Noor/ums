from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsStudentRole


class StudentRegistration(APIView):
    permission_classes = [IsStudentRole]
    def get(self, request):
        return Response({"title": "Registration", "section": "student"}, status=status.HTTP_200_OK)

