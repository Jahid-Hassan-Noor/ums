from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.leave_service import serialize_leave_request
from student_app.models import LeaveRequest
from student_app.registration_service import get_student_profile


class StudentLeave(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        requests = LeaveRequest.objects.select_related("student", "student__user").prefetch_related(
            "approvals",
            "approvals__approver",
            "approvals__approver__user",
            "approvals__class_meeting",
            "approvals__class_meeting__offering",
            "approvals__class_meeting__offering__course",
            "approvals__class_meeting__room",
            "approvals__class_meeting__venue",
        ).filter(student=student)
        return Response(
            {
                "title": "Leave",
                "section": "student",
                "leave_requests": [serialize_leave_request(item) for item in requests],
            },
            status=status.HTTP_200_OK,
        )
