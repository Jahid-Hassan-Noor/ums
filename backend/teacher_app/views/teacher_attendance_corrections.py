from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import Profile
from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import (
    attendance_roster_for_session,
    manual_mark_attendance,
    serialize_session,
    session_for_teacher,
    teacher_sessions,
)


class TeacherAttendanceCorrections(APIView):
    permission_classes = [IsTeacherRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        sessions = list(teacher_sessions(profile))
        selected = session_for_teacher(profile, request.query_params.get("session_id"))
        if not selected and sessions:
            selected = sessions[0]
        return Response(
            {
                "title": "Attendance Corrections",
                "section": "teacher",
                "sessions": [serialize_session(session) for session in sessions],
                "selected_session": serialize_session(selected) if selected else None,
                "students": attendance_roster_for_session(selected) if selected else [],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_teacher_profile(request.user)
        session = session_for_teacher(profile, request.data.get("session_id"))
        if not session:
            return Response(
                {"detail": "Attendance session not found for this teacher."},
                status=status.HTTP_404_NOT_FOUND,
            )
        student = Profile.objects.filter(
            pk=request.data.get("student_id"),
            role=Profile.ROLE_STUDENT,
            is_active=True,
        ).first()
        if not student:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        record, error = manual_mark_attendance(
            session,
            student,
            profile,
            attendance_status=str(request.data.get("attendance_status", "")).strip(),
            reason=str(request.data.get("reason", "")).strip(),
            medical_certificate=request.FILES.get("medical_certificate"),
        )
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "message": "Attendance correction saved.",
                "student": next(
                    (
                        row
                        for row in attendance_roster_for_session(session)
                        if row["student_id"] == student.id
                    ),
                    None,
                ),
                "record_id": record.id,
            },
            status=status.HTTP_200_OK,
        )
