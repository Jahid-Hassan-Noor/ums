from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole


class TeacherCourseRoster(APIView):
    permission_classes = [IsTeacherRole]
    def get(self, request, course_id):
        return Response({"title": "Course Roster", "section": "teacher", "id": course_id}, status=status.HTTP_200_OK)

