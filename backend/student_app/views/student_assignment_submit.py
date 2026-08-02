from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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
    ensure_group_ready,
    group_for_student,
    group_workspace,
)
from teacher_app.assignment_service import (
    assignment_for_student,
    can_submit_assignment,
    upsert_submission,
    validate_submission_files,
)
from teacher_app.models import Assignment, AssignmentSubmission


class StudentAssignmentSubmit(APIView):
    permission_classes = [IsStudentRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, assignment_id):
        student = get_student_profile(request.user)
        assignment = assignment_for_student(student, assignment_id) if student else None
        if not assignment:
            return Response({"detail": "Assignment not found for this student."}, status=status.HTTP_404_NOT_FOUND)
        submission = submission_for_student_assignment(assignment, student)
        return Response(
            {
                "title": "Submit Assignment",
                "section": "student",
                "assignment": serialize_student_assignment(assignment, submission, student=student),
                "submission": serialize_student_submission(submission),
                "group_workspace": group_workspace(assignment, student),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, assignment_id):
        student = get_student_profile(request.user)
        assignment = assignment_for_student(student, assignment_id) if student else None
        if not assignment:
            return Response({"detail": "Assignment not found for this student."}, status=status.HTTP_404_NOT_FOUND)

        assignment_group = None
        if assignment.collaboration_mode == Assignment.COLLABORATION_GROUP:
            assignment_group = group_for_student(assignment, student)
            if not assignment_group:
                return Response(
                    {"detail": "Create or join a group before submitting."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if assignment_group.leader_id != student.id:
                return Response(
                    {"detail": "Only the group leader can submit the final work."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            ensure_group_ready(assignment_group)
        existing = submission_for_student_assignment(assignment, student)
        submission_error = can_submit_assignment(assignment, existing_submission=existing)
        if submission_error:
            return Response({"detail": submission_error}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist("files") or request.FILES.getlist("attachments")
        content = str(request.data.get("content", "")).strip()
        if assignment.submission_type in {Assignment.SUBMISSION_FILE, Assignment.SUBMISSION_BOTH} and not files:
            return Response({"detail": "Upload the required assignment file(s)."}, status=status.HTTP_400_BAD_REQUEST)
        if assignment.submission_type == Assignment.SUBMISSION_TEXT and files:
            return Response({"detail": "This assignment accepts text submissions only."}, status=status.HTTP_400_BAD_REQUEST)

        file_error = validate_submission_files(assignment, files)
        if file_error:
            return Response({"detail": file_error}, status=status.HTTP_400_BAD_REQUEST)

        submission = upsert_submission(
            assignment,
            student,
            content=content,
            files=files,
            assignment_group=assignment_group,
        )
        return Response(
            {
                "message": "Assignment submitted successfully.",
                "assignment": serialize_student_assignment(assignment, submission, student=student),
                "submission": serialize_student_submission(submission),
            },
            status=status.HTTP_201_CREATED,
        )
