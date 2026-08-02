from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from core.media_access import protected_media_url
from student_app.registration_service import get_student_profile
from teacher_app.assignment_service import can_submit_assignment, serialize_assignment, student_assignments
from teacher_app.assignment_group_service import group_for_student, group_rule_status
from teacher_app.models import Assignment, AssignmentSubmission
from teacher_app.serializers import AssignmentSubmissionSerializer


ASSIGNMENT_STATUS_LABELS = {
    "upcoming": "Upcoming",
    "overdue": "Overdue",
    "submitted": "Submitted",
    "graded": "Graded",
}


def serialize_student_submission(submission):
    if not submission:
        return None

    payload = AssignmentSubmissionSerializer(submission).data
    payload["status_label"] = submission.get_status_display()
    payload["attachments"] = [
        {
            "id": attachment.id,
            "file": protected_media_url(attachment.file.name) if attachment.file else "",
            "name": attachment.file.name.rsplit("/", 1)[-1] if attachment.file else "Attachment",
            "uploaded_at": attachment.uploaded_at.isoformat() if attachment.uploaded_at else None,
        }
        for attachment in submission.attachments.all()
    ]
    return payload


def student_assignment_bucket(assignment, submission, now=None):
    now = now or timezone.now()
    if submission:
        if submission.status == AssignmentSubmission.STATUS_GRADED or submission.grade is not None or submission.graded_at:
            return "graded"
        return "submitted"
    if assignment.due_date and assignment.due_date < now:
        return "overdue"
    return "upcoming"


def submission_for_student_assignment(assignment, student):
    if assignment.collaboration_mode == Assignment.COLLABORATION_GROUP:
        group = group_for_student(assignment, student)
        if not group:
            return None
        return (
            AssignmentSubmission.objects.filter(
                assignment=assignment,
                assignment_group=group,
            )
            .prefetch_related("attachments")
            .first()
        )
    return (
        AssignmentSubmission.objects.filter(assignment=assignment, student=student)
        .prefetch_related("attachments")
        .first()
    )


def serialize_student_assignment(assignment, submission=None, now=None, student=None):
    bucket = student_assignment_bucket(assignment, submission, now=now)
    submission_error = can_submit_assignment(assignment, existing_submission=submission)
    if assignment.collaboration_mode == Assignment.COLLABORATION_GROUP and student:
        group = group_for_student(assignment, student)
        if not group:
            submission_error = "Create or join a group before submitting."
        elif group.leader_id != student.id:
            submission_error = "Only the group leader can submit the final work."
        else:
            rule_status = group_rule_status(group)
            if rule_status["violations"]:
                submission_error = rule_status["violations"][0]
    payload = serialize_assignment(assignment)
    payload.update(
        {
            "student_status": bucket,
            "student_status_label": ASSIGNMENT_STATUS_LABELS[bucket],
            "submission": serialize_student_submission(submission),
            "can_submit": submission_error is None,
            "submission_error": submission_error,
            "is_overdue": bucket == "overdue",
        }
    )
    return payload


def assignment_rows_for_student(student):
    if not student:
        return []

    assignments = list(student_assignments(student))
    now = timezone.now()
    return [
        serialize_student_assignment(
            assignment,
            submission_for_student_assignment(assignment, student),
            now=now,
            student=student,
        )
        for assignment in assignments
    ]


def assignment_list_response(request, title, bucket=None):
    student = get_student_profile(request.user)
    rows = assignment_rows_for_student(student)
    counts = {
        "all": len(rows),
        "upcoming": sum(1 for row in rows if row["student_status"] == "upcoming"),
        "overdue": sum(1 for row in rows if row["student_status"] == "overdue"),
        "submitted": sum(1 for row in rows if row["student_status"] == "submitted"),
        "graded": sum(1 for row in rows if row["student_status"] == "graded"),
    }
    filtered_rows = [row for row in rows if row["student_status"] == bucket] if bucket else rows
    return Response(
        {
            "title": title,
            "section": "student",
            "filter": bucket or "all",
            "counts": counts,
            "assignments": filtered_rows,
        },
        status=status.HTTP_200_OK,
    )


class StudentAssignments(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return assignment_list_response(request, "Assignments")
