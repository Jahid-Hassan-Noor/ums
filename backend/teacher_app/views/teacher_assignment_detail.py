from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from notifications_package.service import notify_profile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from core.common.request_utils import parse_bool as _parse_bool, parse_json as _parse_json
from gradebook_app.services import sync_assignment_grade
from teacher_app.assignment_service import (
    assignment_for_teacher,
    get_teacher_profile,
    serialize_assignment,
    serialize_comment,
    serialize_rubric,
    serialize_submission,
)
from teacher_app.assignment_group_service import teacher_group_overview
from teacher_app.models import (
    Assignment,
    AssignmentComment,
    AssignmentFeedback,
    AssignmentRubric,
    AssignmentSubmission,
)


def assignment_detail_payload(assignment):
    submissions = (
        AssignmentSubmission.objects.select_related(
            "student",
            "student__user",
            "graded_by",
            "graded_by__user",
            "assignment_group",
            "assignment_group__leader",
            "assignment_group__leader__user",
        )
        .filter(assignment=assignment)
        .prefetch_related(
            "attachments",
            "feedback_entries",
            "feedback_entries__reviewer",
            "feedback_entries__reviewer__user",
            "comments",
            "comments__author",
            "comments__author__user",
        )
        .order_by("-last_modified_at")
    )
    rubrics = assignment.rubrics.select_related("created_by", "created_by__user").order_by("-is_active", "title")
    comments = assignment.comments.select_related("author", "author__user").filter(submission__isnull=True)
    return {
        "title": "Assignment Detail",
        "section": "teacher",
        "assignment": serialize_assignment(assignment),
        "rubrics": [serialize_rubric(rubric) for rubric in rubrics],
        "comments": [serialize_comment(comment) for comment in comments],
        "groups": teacher_group_overview(assignment),
        "submissions": [serialize_submission(submission) for submission in submissions],
    }


class TeacherAssignmentDetail(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request, assignment_id):
        profile = get_teacher_profile(request.user)
        assignment = assignment_for_teacher(profile, assignment_id)
        if not assignment:
            return Response({"detail": "Assignment not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        return Response(assignment_detail_payload(assignment), status=status.HTTP_200_OK)

    def post(self, request, assignment_id):
        profile = get_teacher_profile(request.user)
        assignment = assignment_for_teacher(profile, assignment_id)
        if not assignment:
            return Response({"detail": "Assignment not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "")).strip().lower()
        message = "Assignment updated."

        with transaction.atomic():
            if action == "save_rubric":
                criteria = _parse_json(request.data.get("criteria"), [])
                rubric = assignment.rubrics.filter(pk=request.data.get("rubric_id")).first()
                if rubric:
                    rubric.title = str(request.data.get("title") or rubric.title).strip()
                    rubric.criteria = criteria if isinstance(criteria, list) else []
                    rubric.max_score = request.data.get("max_score") or assignment.max_score
                    rubric.is_active = _parse_bool(request.data.get("is_active"), True)
                    rubric.save(update_fields=["title", "criteria", "max_score", "is_active", "updated_at"])
                else:
                    AssignmentRubric.objects.create(
                        assignment=assignment,
                        title=str(request.data.get("title") or f"{assignment.title} rubric").strip(),
                        criteria=criteria if isinstance(criteria, list) else [],
                        max_score=request.data.get("max_score") or assignment.max_score,
                        is_active=_parse_bool(request.data.get("is_active"), True),
                        created_by=profile,
                    )
                message = "Rubric saved."

            elif action == "add_comment":
                body = str(request.data.get("body", "")).strip()
                if not body:
                    return Response({"detail": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)
                submission = AssignmentSubmission.objects.filter(
                    pk=request.data.get("submission_id"),
                    assignment=assignment,
                ).first()
                AssignmentComment.objects.create(
                    assignment=assignment,
                    submission=submission,
                    author=profile,
                    body=body,
                    is_private=_parse_bool(request.data.get("is_private"), False),
                )
                message = "Comment added."

            elif action == "grade_submission":
                submission = AssignmentSubmission.objects.select_related("student").filter(
                    pk=request.data.get("submission_id"),
                    assignment=assignment,
                ).first()
                if not submission:
                    return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)
                try:
                    grade = Decimal(str(request.data.get("grade")))
                except (InvalidOperation, TypeError):
                    return Response({"detail": "Enter a valid grade."}, status=status.HTTP_400_BAD_REQUEST)
                if grade < 0 or grade > assignment.max_score:
                    return Response(
                        {"detail": f"Grade must be between 0 and {assignment.max_score}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                feedback = str(request.data.get("feedback", "")).strip()
                rubric = assignment.rubrics.filter(pk=request.data.get("rubric_id"), is_active=True).first()
                rubric_scores = _parse_json(request.data.get("rubric_scores"), {})
                submission.grade = grade
                submission.feedback = feedback
                submission.status = AssignmentSubmission.STATUS_GRADED
                submission.graded_by = profile
                submission.graded_at = timezone.now()
                submission.save(
                    update_fields=["grade", "feedback", "status", "graded_by", "graded_at", "last_modified_at"]
                )
                AssignmentFeedback.objects.create(
                    submission=submission,
                    reviewer=profile,
                    rubric=rubric,
                    rubric_scores=rubric_scores if isinstance(rubric_scores, dict) else {},
                    comments=feedback,
                )
                sync_assignment_grade(submission, actor=profile)
                notify_profile(
                    submission.student,
                    actor=profile,
                    event_type="assignments.graded",
                    verb=f"{assignment.title} has been graded.",
                    data={
                        "assignment_id": assignment.id,
                        "submission_id": submission.id,
                        "grade": str(grade),
                    },
                    url=f"/student/assignments/{assignment.id}",
                )
                message = "Submission graded and feedback returned."

            elif action == "update_status":
                next_status = request.data.get("status")
                allowed = {value for value, _label in Assignment.STATUS_CHOICES}
                if next_status not in allowed:
                    return Response({"detail": "Invalid assignment status."}, status=status.HTTP_400_BAD_REQUEST)
                assignment.status = next_status
                assignment.save(update_fields=["status", "updated_at"])
                message = "Assignment status updated."

            else:
                return Response({"detail": "Unsupported assignment action."}, status=status.HTTP_400_BAD_REQUEST)

        assignment.refresh_from_db()
        return Response(
            {"message": message, **assignment_detail_payload(assignment)},
            status=status.HTTP_200_OK,
        )
