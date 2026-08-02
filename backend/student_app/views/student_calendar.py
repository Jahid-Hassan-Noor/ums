from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsStudentRole
from teacher_app.calendar_service import student_calendar_payload


class StudentCalendar(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(
            student_calendar_payload(request.user),
            status=status.HTTP_200_OK,
        )
