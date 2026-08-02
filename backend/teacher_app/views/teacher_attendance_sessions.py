from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import (
    close_attendance_session,
    generate_qr,
    meeting_for_teacher,
    refresh_qr_if_needed,
    reschedule_or_cancel_class,
    serialize_meeting,
    serialize_session,
    session_for_teacher,
    teacher_sessions,
)
from teacher_app.models import AttendanceSession


class TeacherAttendanceSessions(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        return Response(
            {
                "title": "Attendance Sessions",
                "section": "teacher",
                "sessions": [
                    serialize_session(
                        session,
                        include_token=session.status == AttendanceSession.STATUS_OPEN,
                    )
                    for session in teacher_sessions(profile)
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_teacher_profile(request.user)
        action = str(request.data.get("action", "refresh_qr")).strip().lower()
        session = session_for_teacher(profile, request.data.get("session_id"))
        if not session:
            return Response({"detail": "Attendance session not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        if action == "close":
            session = close_attendance_session(session)
            return Response(
                {"message": "Attendance QR closed.", "session": serialize_session(session)},
                status=status.HTTP_200_OK,
            )
        if session.status != AttendanceSession.STATUS_OPEN:
            return Response(
                {"detail": "Only open attendance sessions can generate a QR code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if action == "regenerate_qr":
            generate_qr(session)
            session.refresh_from_db()
        else:
            session = refresh_qr_if_needed(session)
        return Response(
            {"message": "Attendance QR refreshed.", "session": serialize_session(session, include_token=True)},
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        profile = get_teacher_profile(request.user)
        meeting = meeting_for_teacher(profile, request.data.get("class_meeting_id"))
        if not meeting:
            return Response({"detail": "Class meeting not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        updated = reschedule_or_cancel_class(profile, meeting, request.data)
        return Response(
            {
                "message": "Class schedule updated.",
                "meeting": serialize_meeting(updated),
            },
            status=status.HTTP_200_OK,
        )
