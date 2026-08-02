from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from admin_app.hostel_student_life import hostel_student_life_payload
from auth_app.permissions import IsStudentRole


class StudentWardenSchedule(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student_life = hostel_student_life_payload()
        return Response(
            {
                "title": "Warden Schedule",
                "section": "student",
                "schedule": student_life["warden_schedule"],
                "updated_at": student_life["updated_at"],
            },
            status=status.HTTP_200_OK,
        )
