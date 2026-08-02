from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from student_app.leave_service import decide_leave_approval, serialize_leave_request
from student_app.models import LeaveApproval, LeaveRequest
from teacher_app.assignment_service import get_teacher_profile


class TeacherLeaveRequests(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        approvals = LeaveApproval.objects.select_related(
            "leave_request",
            "leave_request__student",
            "leave_request__student__user",
            "approver",
            "approver__user",
            "class_meeting",
            "class_meeting__offering",
            "class_meeting__offering__course",
        ).filter(approver=profile).order_by("-created_at")
        leave_ids = approvals.values_list("leave_request_id", flat=True)
        leave_requests = LeaveRequest.objects.select_related("student", "student__user").prefetch_related(
            "approvals",
            "approvals__approver",
            "approvals__approver__user",
            "approvals__class_meeting",
            "approvals__class_meeting__offering",
            "approvals__class_meeting__offering__course",
            "approvals__class_meeting__room",
            "approvals__class_meeting__venue",
        ).filter(pk__in=leave_ids).distinct()
        return Response(
            {
                "title": "Leave Requests",
                "section": "teacher",
                "approver_profile_id": profile.id,
                "leave_requests": [
                    serialize_leave_request(item, viewer=profile) for item in leave_requests
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_teacher_profile(request.user)
        approval = LeaveApproval.objects.select_related(
            "leave_request",
            "leave_request__student",
            "leave_request__student__user",
        ).filter(pk=request.data.get("approval_id"), approver=profile).first()
        if not approval:
            return Response({"detail": "Leave approval request not found."}, status=status.HTTP_404_NOT_FOUND)
        error = decide_leave_approval(
            approval,
            decision=str(request.data.get("decision", "")).strip().lower(),
            note=str(request.data.get("note", "")).strip(),
        )
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        approval.leave_request.refresh_from_db()
        return Response(
            {
                "message": "Leave decision recorded.",
                "leave_request": serialize_leave_request(approval.leave_request, viewer=profile),
            },
            status=status.HTTP_200_OK,
        )
