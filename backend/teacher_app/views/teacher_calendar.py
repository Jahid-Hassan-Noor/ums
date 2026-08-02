from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole
from teacher_app.calendar_service import teacher_calendar_payload


class TeacherCalendar(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        return Response(
            teacher_calendar_payload(request.user),
            status=status.HTTP_200_OK,
        )
