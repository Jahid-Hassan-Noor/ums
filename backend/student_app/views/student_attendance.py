from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.registration_service import get_student_profile
from teacher_app.attendance_service import (
    student_attendance_semester,
    student_attendance_semesters,
    student_attendance_summary,
)


class StudentAttendance(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        semester = student_attendance_semester(student, request.query_params.get("semester_id"))
        return Response(
            {
                "title": "Attendance",
                "section": "student",
                "semester": {"id": semester.id, "name": semester.name} if semester else None,
                "semesters": student_attendance_semesters(student),
                "courses": student_attendance_summary(student, semester=semester) if student else [],
            },
            status=status.HTTP_200_OK,
        )
