from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole


class TeacherUms(APIView):
    permission_classes = [IsTeacherRole]
    def get(self, request):
        return Response({"title": "Teacher Portal", "section": "teacher"}, status=status.HTTP_200_OK)

