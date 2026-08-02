from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsStudentRole
from admin_app.schedule import schedule_payload_for_role


class StudentTimetable(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(
            schedule_payload_for_role("student", "Timetable", "student", user=request.user),
            status=status.HTTP_200_OK,
        )
