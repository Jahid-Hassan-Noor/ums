from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import (
    serialize_meeting,
    serialize_session,
    teacher_meetings,
    teacher_sessions,
)
from teacher_app.models import AttendanceSession


class TeacherAttendance(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        return Response(
            {
                "title": "Attendance",
                "section": "teacher",
                "meetings": [serialize_meeting(meeting) for meeting in teacher_meetings(profile)],
                "sessions": [
                    serialize_session(
                        session,
                        include_token=session.status == AttendanceSession.STATUS_OPEN,
                    )
                    for session in teacher_sessions(profile)[:10]
                ],
            },
            status=status.HTTP_200_OK,
        )
