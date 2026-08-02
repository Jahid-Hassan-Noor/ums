from django.db.models import Q
from django.utils import timezone

from admin_app.models import CourseOffering, Profile
from admin_app.settings_registry import setting_value
from core.common.profiles import get_teacher_profile, profile_display_name
from core.media_access import protected_media_url
from core.upload_security import (
    ALLOWED_IMAGE_EXTENSIONS_DOTTED,
    image_file_extension,
    image_upload_error,
)
from notifications_package.service import notify_profiles
from student_app.models import Enrollment
from teacher_app.models import (
    Assignment,
    AssignmentAttachment,
    AssignmentComment,
    AssignmentFeedback,
    AssignmentRubric,
    AssignmentSubmission,
)


FILE_EXTENSIONS = {
    Assignment.FILE_DOC: {".doc", ".docx"},
    Assignment.FILE_PDF: {".pdf"},
    Assignment.FILE_ZIP: {".zip"},
    Assignment.FILE_PRESENTATION: {".ppt", ".pptx"},
    Assignment.FILE_IMAGE: ALLOWED_IMAGE_EXTENSIONS_DOTTED,
    Assignment.FILE_SPREADSHEET: {".xls", ".xlsx", ".csv"},
}


def accepted_file_types(assignment):
    return assignment.accepted_file_types or [assignment.accepted_file_type]


def accepted_extensions(assignment):
    return sorted(
        {
            extension
            for file_type in accepted_file_types(assignment)
            for extension in FILE_EXTENSIONS.get(file_type, set())
        }
    )


def teacher_offerings(profile, *, include_inactive=False):
    if not profile:
        return CourseOffering.objects.none()
    queryset = (
        CourseOffering.objects.select_related("course", "semester")
        .filter(Q(instructor=profile) | Q(class_meetings__lecturer=profile))
        .distinct()
        .order_by("-semester__start_date", "course__code", "section")
    )
    return queryset if include_inactive else queryset.filter(is_active=True)


def serialize_assignment(assignment, include_offering=True):
    payload = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "instructions": assignment.instructions,
        "file_instructions": assignment.file_instructions,
        "opens_at": assignment.opens_at.isoformat() if assignment.opens_at else None,
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "cutoff_at": assignment.cutoff_at.isoformat() if assignment.cutoff_at else None,
        "max_score": str(assignment.max_score),
        "activity_kind": assignment.activity_kind,
        "activity_kind_label": assignment.get_activity_kind_display(),
        "collaboration_mode": assignment.collaboration_mode,
        "collaboration_mode_label": assignment.get_collaboration_mode_display(),
        "max_group_members": assignment.max_group_members,
        "require_same_tutorial_group": assignment.require_same_tutorial_group,
        "require_same_lab_group": assignment.require_same_lab_group,
        "min_distinct_countries": assignment.min_distinct_countries,
        "group_rules": assignment.group_rules,
        "submission_type": assignment.submission_type,
        "accepted_file_type": assignment.accepted_file_type,
        "accepted_file_types": accepted_file_types(assignment),
        "accepted_extensions": accepted_extensions(assignment),
        "max_files": assignment.max_files,
        "max_file_size_mb": assignment.max_file_size_mb,
        "allow_multiple_submissions": assignment.allow_multiple_submissions,
        "allow_late_submissions": assignment.allow_late_submissions,
        "status": assignment.status,
        "created_by": profile_display_name(assignment.created_by),
        "submission_count": getattr(assignment, "submission_count", None),
        "graded_count": getattr(assignment, "graded_count", None),
    }
    if include_offering:
        payload["offering"] = {
            "id": assignment.offering_id,
            "course_code": assignment.offering.course.code,
            "course_title": assignment.offering.course.title,
            "section": assignment.offering.section,
            "semester": assignment.offering.semester.name,
        }
    return payload


def serialize_attachment(attachment):
    return {
        "id": attachment.id,
        "file": protected_media_url(attachment.file.name) if attachment.file else "",
        "name": attachment.file.name.rsplit("/", 1)[-1] if attachment.file else "Attachment",
        "uploaded_at": attachment.uploaded_at.isoformat() if attachment.uploaded_at else None,
    }


def serialize_rubric(rubric):
    return {
        "id": rubric.id,
        "title": rubric.title,
        "criteria": rubric.criteria or [],
        "max_score": str(rubric.max_score),
        "is_active": rubric.is_active,
        "created_by": profile_display_name(rubric.created_by),
    }


def serialize_comment(comment):
    return {
        "id": comment.id,
        "body": comment.body,
        "is_private": comment.is_private,
        "author": profile_display_name(comment.author),
        "author_role": comment.author.role if comment.author else "",
        "submission_id": comment.submission_id,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
    }


def serialize_feedback(feedback):
    return {
        "id": feedback.id,
        "reviewer": profile_display_name(feedback.reviewer),
        "rubric_id": feedback.rubric_id,
        "rubric_scores": feedback.rubric_scores or {},
        "comments": feedback.comments,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
    }


def serialize_submission(submission):
    payload = {
        "id": submission.id,
        "student": {
            "id": submission.student_id,
            "name": profile_display_name(submission.student),
            "username": submission.student.user.username,
        },
        "content": submission.content,
        "attempt_count": submission.attempt_count,
        "status": submission.status,
        "status_label": submission.get_status_display(),
        "grade": str(submission.grade) if submission.grade is not None else None,
        "feedback": submission.feedback,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "last_modified_at": submission.last_modified_at.isoformat() if submission.last_modified_at else None,
        "graded_by": profile_display_name(submission.graded_by),
        "graded_at": submission.graded_at.isoformat() if submission.graded_at else None,
        "attachments": [serialize_attachment(attachment) for attachment in submission.attachments.all()],
        "feedback_entries": [serialize_feedback(entry) for entry in submission.feedback_entries.all()],
        "comments": [serialize_comment(comment) for comment in submission.comments.all()],
    }
    if submission.assignment_group_id:
        payload["assignment_group"] = {
            "id": submission.assignment_group_id,
            "name": submission.assignment_group.name,
            "leader_id": submission.assignment_group.leader_id,
        }
    else:
        payload["assignment_group"] = None
    return payload


def assignment_for_teacher(profile, assignment_id):
    return (
        Assignment.objects.select_related("offering", "offering__course", "offering__semester", "created_by", "created_by__user")
        .filter(pk=assignment_id, offering__in=teacher_offerings(profile))
        .first()
    )


def student_assignments(student):
    offering_ids = Enrollment.objects.filter(student=student, completed_at__isnull=True).values("offering_id")
    return (
        Assignment.objects.select_related("offering", "offering__course", "offering__semester", "created_by", "created_by__user")
        .filter(offering_id__in=offering_ids)
        .exclude(status=Assignment.STATUS_DRAFT)
        .order_by("due_date", "title")
    )


def assignment_for_student(student, assignment_id):
    return student_assignments(student).filter(pk=assignment_id).first()


def notify_assignment_students(assignment):
    if not setting_value("notifications", "notify_assignments"):
        return
    enrollments = Enrollment.objects.select_related("student").filter(
        offering=assignment.offering,
        completed_at__isnull=True,
    )
    notify_profiles(
        [enrollment.student for enrollment in enrollments],
        actor=assignment.created_by,
        event_type="assignments.published",
        verb=f"New assignment posted: {assignment.title}",
        data={
            "assignment_id": assignment.id,
            "course_code": assignment.offering.course.code,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        },
        url=f"/student/assignments/{assignment.id}",
    )


def notify_assignment_submission(submission):
    if not setting_value("notifications", "notify_assignments"):
        return
    assignment = submission.assignment
    recipient_ids = {
        assignment.created_by_id,
        assignment.offering.instructor_id,
        *assignment.offering.class_meetings.values_list("lecturer_id", flat=True),
    }
    notify_profiles(
        [recipient_id for recipient_id in recipient_ids if recipient_id],
        actor=submission.student,
        event_type="assignments.submitted",
        verb=f"{profile_display_name(submission.student)} submitted {assignment.title}.",
        data={
            "assignment_id": assignment.id,
            "submission_id": submission.id,
            "course_code": assignment.offering.course.code,
            "attempt_count": submission.attempt_count,
            "status": submission.status,
        },
        url=f"/teacher/assignments/{assignment.id}/submissions",
    )


def validate_submission_files(assignment, files):
    if len(files) > assignment.max_files:
        return f"This assignment allows up to {assignment.max_files} file(s)."
    allowed = set(accepted_extensions(assignment))
    max_bytes = assignment.max_file_size_mb * 1024 * 1024
    for upload in files:
        name = upload.name.lower()
        if not any(name.endswith(extension) for extension in allowed):
            readable = ", ".join(sorted(allowed))
            return f"{upload.name} is not allowed. Submit {readable} file(s)."
        if upload.size > max_bytes:
            return f"{upload.name} exceeds the {assignment.max_file_size_mb} MB per-file limit."
        extension = f".{image_file_extension(upload)}"
        if extension in ALLOWED_IMAGE_EXTENSIONS_DOTTED:
            error = image_upload_error(
                upload,
                field_label=upload.name,
                max_bytes=max_bytes,
                max_size_label=f"{assignment.max_file_size_mb} MB",
            )
            if error:
                return error
    return None


def can_submit_assignment(assignment, existing_submission=None):
    now = timezone.now()
    if assignment.opens_at and now < assignment.opens_at:
        return "This assignment is not open yet."
    if assignment.cutoff_at and now > assignment.cutoff_at:
        return "The assignment cutoff time has passed."
    if assignment.due_date and now > assignment.due_date and not assignment.allow_late_submissions:
        return "Late submissions are not allowed for this assignment."
    if (
        existing_submission
        and existing_submission.attempt_count > 0
        and not assignment.allow_multiple_submissions
    ):
        return "This assignment allows only one submission."
    return None


def upsert_submission(assignment, student, *, content="", files=None, assignment_group=None):
    files = files or []
    submission, _created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student,
        defaults={"content": content, "assignment_group": assignment_group},
    )
    submission.content = content
    submission.assignment_group = assignment_group
    submission.attempt_count = (submission.attempt_count or 0) + 1
    submission.status = (
        AssignmentSubmission.STATUS_LATE
        if assignment.due_date and timezone.now() > assignment.due_date
        else AssignmentSubmission.STATUS_SUBMITTED
    )
    submission.save(
        update_fields=[
            "content",
            "assignment_group",
            "attempt_count",
            "status",
            "last_modified_at",
        ]
    )

    submission.attachments.all().delete()
    for upload in files:
        AssignmentAttachment.objects.create(submission=submission, file=upload)
    notify_assignment_submission(submission)
    return submission
