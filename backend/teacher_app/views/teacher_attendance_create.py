from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import (
    meeting_attendance_window,
    meeting_for_teacher,
    serialize_meeting,
    serialize_session,
    start_attendance_session,
    teacher_meetings,
)


class TeacherAttendanceCreate(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        return Response(
            {
                "title": "Create Attendance Session",
                "section": "teacher",
                "meetings": [serialize_meeting(meeting) for meeting in teacher_meetings(profile)],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_teacher_profile(request.user)
        meeting = meeting_for_teacher(profile, request.data.get("class_meeting_id"))
        if not meeting:
            return Response({"detail": "Class meeting not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        session_date = parse_date(str(request.data.get("session_date") or "")) or None
        window = meeting_attendance_window(meeting)
        if session_date and session_date != timezone.localdate():
            return Response(
                {"detail": "Attendance sessions can only be opened for today's scheduled class."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not window["can_open"]:
            return Response({"detail": window["reason"]}, status=status.HTTP_400_BAD_REQUEST)
        session = start_attendance_session(
            profile,
            meeting,
            session_date=session_date,
            start_time=request.data.get("start_time"),
            end_time=request.data.get("end_time"),
        )
        return Response(
            {
                "message": "Attendance session started.",
                "session": serialize_session(session, include_token=True),
            },
            status=status.HTTP_201_CREATED,
        )
