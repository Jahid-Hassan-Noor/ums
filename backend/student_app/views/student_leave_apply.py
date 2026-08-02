from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from admin_app.settings_registry import setting_value
from student_app.leave_service import serialize_leave_request, submit_leave_request
from student_app.registration_service import get_student_profile


class StudentLeaveApply(APIView):
    permission_classes = [IsStudentRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(
            {
                "title": "Apply Leave",
                "section": "student",
                "required_fields": ["start_date", "end_date", "reason"],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        student = get_student_profile(request.user)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        start_date = parse_date(str(request.data.get("start_date") or ""))
        end_date = parse_date(str(request.data.get("end_date") or ""))
        reason = str(request.data.get("reason", "")).strip()
        if not start_date or not end_date:
            return Response({"detail": "Leave start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)
        if start_date > end_date:
            return Response({"detail": "Leave end_date must be after start_date."}, status=status.HTTP_400_BAD_REQUEST)
        minimum_notice = setting_value("workflow", "leave_request_min_notice_days")
        if start_date < timezone.localdate() + timedelta(days=minimum_notice):
            return Response(
                {"detail": f"Leave requests require at least {minimum_notice} day(s) notice."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not reason:
            return Response({"detail": "Leave reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        leave_request = submit_leave_request(
            student,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            attachment=request.FILES.get("attachment"),
        )
        return Response(
            {
                "message": "Leave request submitted.",
                "leave_request": serialize_leave_request(leave_request),
            },
            status=status.HTTP_201_CREATED,
        )
