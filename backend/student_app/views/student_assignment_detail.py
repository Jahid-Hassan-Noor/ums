from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.registration_service import get_student_profile
from student_app.views.student_assignments import (
    serialize_student_assignment,
    serialize_student_submission,
    submission_for_student_assignment,
)
from teacher_app.assignment_group_service import (
    create_group,
    delete_group,
    group_for_student,
    group_workspace,
    invite_student,
    leave_group,
    remove_group_member,
    respond_to_invitation,
)
from teacher_app.assignment_service import (
    assignment_for_student,
    serialize_comment,
    serialize_rubric,
)
from teacher_app.models import (
    AssignmentComment,
    AssignmentGroupInvitation,
)


def student_assignment_detail_payload(assignment, student):
    submission = submission_for_student_assignment(assignment, student)
    return {
        "title": "Assignment Detail",
        "section": "student",
        "assignment": serialize_student_assignment(
            assignment,
            submission,
            student=student,
        ),
        "submission": serialize_student_submission(submission),
        "group_workspace": group_workspace(assignment, student),
        "rubrics": [
            serialize_rubric(rubric)
            for rubric in assignment.rubrics.select_related(
                "created_by",
                "created_by__user",
            ).filter(is_active=True)
        ],
        "comments": [
            serialize_comment(comment)
            for comment in assignment.comments.select_related("author", "author__user")
            .filter(is_private=False)
            .filter(submission__isnull=True)
        ],
    }


class StudentAssignmentDetail(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request, assignment_id):
        student = get_student_profile(request.user)
        assignment = assignment_for_student(student, assignment_id) if student else None
        if not assignment:
            return Response({"detail": "Assignment not found for this student."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            student_assignment_detail_payload(assignment, student),
            status=status.HTTP_200_OK,
        )

    def post(self, request, assignment_id):
        student = get_student_profile(request.user)
        assignment = assignment_for_student(student, assignment_id) if student else None
        if not assignment:
            return Response({"detail": "Assignment not found for this student."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "add_comment")).strip().lower()
        message = "Assignment updated."
        if action == "create_group":
            create_group(assignment, student, request.data.get("name"))
            message = "Group created. You are the group leader."
        elif action == "invite_member":
            group = group_for_student(assignment, student)
            if not group:
                return Response({"detail": "Create a group first."}, status=status.HTTP_400_BAD_REQUEST)
            invite_student(group, student, request.data.get("student_id"))
            message = "Group invitation sent."
        elif action in {"accept_invitation", "decline_invitation"}:
            invitation = AssignmentGroupInvitation.objects.filter(
                pk=request.data.get("invitation_id"),
                assignment=assignment,
                invitee=student,
            ).first()
            if not invitation:
                return Response({"detail": "Invitation not found."}, status=status.HTTP_404_NOT_FOUND)
            respond_to_invitation(invitation, student, action == "accept_invitation")
            message = "Invitation accepted." if action == "accept_invitation" else "Invitation declined."
        elif action == "remove_member":
            group = group_for_student(assignment, student)
            if not group:
                return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
            remove_group_member(group, student, request.data.get("student_id"))
            message = "Group member removed."
        elif action in {"delete_group", "leave_group"}:
            group = group_for_student(assignment, student)
            if not group:
                return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
            if action == "delete_group":
                delete_group(group, student)
                message = "Group deleted."
            else:
                leave_group(group, student)
                message = "You left the group."
        elif action == "add_comment":
            body = str(request.data.get("body", "")).strip()
            if not body:
                return Response({"detail": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)
            submission = submission_for_student_assignment(assignment, student)
            AssignmentComment.objects.create(
                assignment=assignment,
                submission=submission if request.data.get("submission_comment") else None,
                author=student,
                body=body,
                is_private=False,
            )
            message = "Comment added."
        else:
            return Response({"detail": "Unsupported assignment action."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": message, **student_assignment_detail_payload(assignment, student)},
            status=status.HTTP_201_CREATED if action == "add_comment" else status.HTTP_200_OK,
        )
