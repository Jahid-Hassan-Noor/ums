from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import Profile
from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import (
    attendance_summary_for_offering,
    manual_mark_attendance,
    send_low_attendance_warnings,
    serialize_session,
    session_for_teacher,
    teacher_sessions,
)
from teacher_app.course_content_service import offering_for_teacher
from teacher_app.models import AttendanceSession


class TeacherCourseAttendance(APIView):
    permission_classes = [IsTeacherRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, course_id):
        profile = get_teacher_profile(request.user)
        offering = offering_for_teacher(profile, course_id)
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        sessions = teacher_sessions(profile).filter(offering=offering)
        return Response(
            {
                "title": "Course Attendance",
                "section": "teacher",
                "course": {
                    "id": offering.id,
                    "code": offering.course.code,
                    "title": offering.course.title,
                    "section": offering.section,
                },
                "sessions": [
                    serialize_session(
                        session,
                        include_token=session.status == AttendanceSession.STATUS_OPEN,
                    )
                    for session in sessions
                ],
                "students": attendance_summary_for_offering(offering),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, course_id):
        profile = get_teacher_profile(request.user)
        offering = offering_for_teacher(profile, course_id)
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "mark")).strip().lower()
        if action == "send_warnings":
            warned = send_low_attendance_warnings(offering, profile)
            return Response(
                {
                    "message": f"Attendance warning sent to {len(warned)} student(s).",
                    "students": warned,
                },
                status=status.HTTP_200_OK,
            )

        session = session_for_teacher(profile, request.data.get("session_id"))
        if not session or session.offering_id != offering.id:
            return Response({"detail": "Attendance session not found for this course."}, status=status.HTTP_404_NOT_FOUND)
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
                "message": "Attendance marked.",
                "record": {
                    "id": record.id,
                    "student_id": record.student_id,
                    "attendance_status": record.attendance_status,
                    "present": record.present,
                    "reason": record.reason,
                },
            },
            status=status.HTTP_200_OK,
        )
