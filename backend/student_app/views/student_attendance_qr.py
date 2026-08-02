from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.registration_service import get_student_profile
from teacher_app.attendance_service import (
    eligible_student_for_session,
    serialize_session,
    submit_qr_attendance,
)
from teacher_app.models import AttendanceSession


class StudentAttendanceQR(APIView):
    permission_classes = [IsStudentRole]

    def find_session(self, *, session_id=None, code=""):
        sessions = AttendanceSession.objects.select_related(
            "offering",
            "offering__course",
            "class_meeting",
            "class_meeting__tutorial_group",
            "class_meeting__lab_group",
            "created_by",
        )
        if session_id:
            return sessions.filter(pk=session_id).first()
        if code:
            return sessions.filter(qr_token=code).first()
        return None

    def get(self, request):
        student = get_student_profile(request.user)
        code = str(request.query_params.get("code", "")).strip().lower()
        session = self.find_session(
            session_id=request.query_params.get("session_id"),
            code=code,
        )
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        if session and not eligible_student_for_session(student, session):
            return Response(
                {"detail": "You are not enrolled in this class group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {
                "title": "Attendance QR",
                "section": "student",
                "session": serialize_session(session) if session else None,
                "code": code,
                "is_valid": bool(
                    session
                    and session.status == AttendanceSession.STATUS_OPEN
                    and session.qr_token == code
                    and session.qr_expires_at
                    and session.qr_expires_at > timezone.now()
                ),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        student = get_student_profile(request.user)
        token = str(request.data.get("token", request.data.get("code", ""))).strip().lower()
        session = self.find_session(
            session_id=request.data.get("session_id"),
            code=token,
        )
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        if not session:
            return Response(
                {"detail": "Attendance code is invalid or has already been replaced."},
                status=status.HTTP_404_NOT_FOUND,
            )
        submission = submit_qr_attendance(
            student,
            session=session,
            token=token,
            ip_address=request.META.get("REMOTE_ADDR", ""),
        )
        response_status = status.HTTP_200_OK if submission.status == "accepted" else status.HTTP_400_BAD_REQUEST
        return Response(
            {
                "message": submission.message,
                "submission": {
                    "id": submission.id,
                    "status": submission.status,
                    "message": submission.message,
                    "submitted_at": submission.submitted_at.isoformat(),
                },
            },
            status=response_status,
        )
