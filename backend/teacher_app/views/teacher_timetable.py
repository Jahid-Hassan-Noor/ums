from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole
from admin_app.schedule import schedule_payload_for_role


class TeacherTimetable(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        return Response(
            schedule_payload_for_role(
                "teacher",
                "Timetable",
                "teacher",
                user=request.user,
            ),
            status=status.HTTP_200_OK,
        )
