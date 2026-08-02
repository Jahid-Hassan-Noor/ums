from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole


class TeacherNotifications(APIView):
    permission_classes = [IsTeacherRole]
    def get(self, request):
        return Response({"title": "Notifications", "section": "teacher"}, status=status.HTTP_200_OK)

