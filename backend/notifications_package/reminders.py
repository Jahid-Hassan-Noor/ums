from collections import defaultdict
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from admin_app.settings_registry import setting_value
from auth_app.models import Profile
from executive_app.models import CourseEvaluationResponse, CourseEvaluationSurvey
from librarian_app.models import Loan
from notifications_package.models import Notification
from notifications_package.service import notify_profile, notify_profiles
from student_app.models import Enrollment
from teacher_app.models import (
    Assignment,
    AssignmentGroupMembership,
    AssignmentSubmission,
)


REMINDER_WINDOW = timedelta(hours=2)
PROFILE_THROTTLE_SECONDS = 60
EVALUATION_OPENED_EVENT = "evaluations.opened"
EVALUATION_CLOSING_SOON_EVENT = "evaluations.closing_soon"
SUBMITTED_STATUSES = {
    AssignmentSubmission.STATUS_SUBMITTED,
    AssignmentSubmission.STATUS_LATE,
    AssignmentSubmission.STATUS_GRADED,
    AssignmentSubmission.STATUS_RETURNED,
}


def _eligible_student_profiles(profile=None):
    profiles = Profile.objects.filter(
        role=Profile.ROLE_STUDENT,
        is_active=True,
        user__is_active=True,
    )
    return profiles.filter(pk=profile.pk) if profile else profiles


def _existing_reminder_keys(event_type, object_key, recipient_ids):
    keys = set()
    notifications = Notification.objects.filter(
        recipient_id__in=recipient_ids,
        data__event_type=event_type,
    ).values_list("recipient_id", "data")
    for recipient_id, data in notifications:
        object_id = (data or {}).get(object_key)
        if object_id is not None:
            keys.add((recipient_id, object_id))
    return keys


def _loan_asset_label(loan):
    if loan.book_copy_id:
        return loan.book_copy.book.title
    if loan.laptop_id:
        return f"{loan.laptop.brand} {loan.laptop.model}".strip() or loan.laptop.asset_tag
    if loan.room_id:
        return loan.room.name
    return "library item"


def _format_due_at(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d %b %Y, %I:%M %p")


def _survey_course_label(survey):
    course = survey.offering.course
    return f"{course.code} {course.title}".strip()


def _required_survey_queryset():
    return CourseEvaluationSurvey.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
    ).filter(
        is_published=True,
        is_required=True,
    )


def _opened_required_surveys(now):
    return _required_survey_queryset().filter(
        opens_at__isnull=False,
        opens_at__gt=now - REMINDER_WINDOW,
        opens_at__lte=now,
        closes_at__gt=now,
    )


def _closing_required_surveys(now):
    return _required_survey_queryset().filter(
        opens_at__lte=now,
        closes_at__gt=now,
        closes_at__lte=now + REMINDER_WINDOW,
    )


def _unsubmitted_survey_recipients(survey, recipient_ids):
    submitted_student_ids = set(
        CourseEvaluationResponse.objects.filter(survey=survey).values_list(
            "student_id",
            flat=True,
        )
    )
    return [
        enrollment.student
        for enrollment in Enrollment.objects.select_related("student", "student__user")
        .filter(
            student_id__in=recipient_ids,
            offering=survey.offering,
        )
        .order_by("student_id")
        if enrollment.student_id not in submitted_student_ids
    ]


def _send_survey_reminder_batch(*, surveys, recipient_ids, event_type):
    existing = _existing_reminder_keys(event_type, "survey_id", recipient_ids)
    created_count = 0
    for survey in surveys:
        recipients = [
            recipient
            for recipient in _unsubmitted_survey_recipients(survey, recipient_ids)
            if (recipient.id, survey.id) not in existing
        ]
        if not recipients:
            continue

        course_label = _survey_course_label(survey)
        url = f"/student/evaluations/{survey.id}"
        if event_type == EVALUATION_OPENED_EVENT:
            verb = f"Required SEC-SET evaluation for {course_label} is now open."
            email_subject = f"SEC-SET evaluation is open: {survey.offering.course.code}"
            email_message = (
                f"The required SEC-SET evaluation for {course_label} is now open."
            )
            if survey.closes_at:
                email_message += f" Complete it before {_format_due_at(survey.closes_at)}."
        else:
            verb = f"Required SEC-SET evaluation for {course_label} closes within 2 hours."
            email_subject = f"SEC-SET evaluation closes soon: {survey.offering.course.code}"
            email_message = (
                f"The required SEC-SET evaluation for {course_label} closes within 2 hours."
            )
            if survey.closes_at:
                email_message += f" Submit it before {_format_due_at(survey.closes_at)}."

        notify_profiles(
            recipients,
            event_type=event_type,
            verb=verb,
            data={
                "survey_id": survey.id,
                "course_code": survey.offering.course.code,
                "opens_at": survey.opens_at.isoformat() if survey.opens_at else None,
                "closes_at": survey.closes_at.isoformat() if survey.closes_at else None,
            },
            url=url,
            email_subject=email_subject,
            email_message=email_message,
        )
        for recipient in recipients:
            existing.add((recipient.id, survey.id))
        created_count += len(recipients)
    return created_count


def send_library_due_reminders(*, profile=None, now=None):
    if not setting_value("notifications", "notify_library_due_reminders"):
        return 0

    now = now or timezone.now()
    profiles = list(_eligible_student_profiles(profile))
    recipient_ids = [student.id for student in profiles]
    if not recipient_ids:
        return 0

    loans = (
        Loan.objects.select_related(
            "student",
            "book_copy__book",
            "laptop",
            "room",
        )
        .filter(
            student_id__in=recipient_ids,
            status=Loan.STATUS_ACTIVE,
            due_at__gt=now,
            due_at__lte=now + REMINDER_WINDOW,
        )
        .order_by("due_at", "id")
    )
    existing = _existing_reminder_keys(
        "library.loan_due_soon",
        "loan_id",
        recipient_ids,
    )
    created_count = 0
    for loan in loans:
        key = (loan.student_id, loan.id)
        if key in existing:
            continue
        notify_profile(
            loan.student,
            event_type="library.loan_due_soon",
            verb=(
                f"Return the key for {_loan_asset_label(loan)} within 2 hours."
                if loan.room_id
                else f"Return {_loan_asset_label(loan)} within 2 hours to avoid an overdue loan."
            ),
            data={
                "loan_id": loan.id,
                "due_at": loan.due_at.isoformat(),
                "asset_type": "book" if loan.book_copy_id else "laptop" if loan.laptop_id else "room",
            },
            url=(
                "/student/library/books"
                if loan.book_copy_id
                else "/student/library/laptops"
                if loan.laptop_id
                else "/student/library/rooms"
            ),
        )
        existing.add(key)
        created_count += 1
    return created_count


def send_required_evaluation_reminders(*, profile=None, now=None):
    if not setting_value("notifications", "notify_sec_set_reminders"):
        return 0

    now = now or timezone.now()
    profiles = list(_eligible_student_profiles(profile).select_related("user"))
    recipient_ids = [student.id for student in profiles]
    if not recipient_ids:
        return 0

    opened_count = _send_survey_reminder_batch(
        surveys=_opened_required_surveys(now).order_by("opens_at", "id"),
        recipient_ids=recipient_ids,
        event_type=EVALUATION_OPENED_EVENT,
    )
    closing_count = _send_survey_reminder_batch(
        surveys=_closing_required_surveys(now).order_by("closes_at", "id"),
        recipient_ids=recipient_ids,
        event_type=EVALUATION_CLOSING_SOON_EVENT,
    )
    return opened_count + closing_count


def send_assignment_due_reminders(*, profile=None, now=None):
    if not setting_value("notifications", "notify_assignments"):
        return 0

    now = now or timezone.now()
    profiles = list(_eligible_student_profiles(profile).select_related("user"))
    recipient_ids = [student.id for student in profiles]
    if not recipient_ids:
        return 0

    assignments = list(
        Assignment.objects.select_related(
            "offering__course",
            "created_by",
        )
        .filter(
            status=Assignment.STATUS_PUBLISHED,
            due_date__gt=now,
            due_date__lte=now + REMINDER_WINDOW,
        )
        .order_by("due_date", "id")
    )
    if not assignments:
        return 0

    assignments_by_offering = defaultdict(list)
    for assignment in assignments:
        assignments_by_offering[assignment.offering_id].append(assignment)

    enrollments = list(
        Enrollment.objects.select_related("student").filter(
            student_id__in=recipient_ids,
            offering_id__in=assignments_by_offering,
            completed_at__isnull=True,
        )
    )
    assignment_ids = [assignment.id for assignment in assignments]
    submitted_rows = AssignmentSubmission.objects.filter(
        assignment_id__in=assignment_ids,
        status__in=SUBMITTED_STATUSES,
    ).values_list("assignment_id", "student_id", "assignment_group_id")
    submitted_individual = set()
    submitted_groups = set()
    for assignment_id, student_id, group_id in submitted_rows:
        if group_id:
            submitted_groups.add((assignment_id, group_id))
        else:
            submitted_individual.add((assignment_id, student_id))

    group_memberships = {
        (assignment_id, student_id): group_id
        for assignment_id, student_id, group_id in AssignmentGroupMembership.objects.filter(
            assignment_id__in=assignment_ids,
            student_id__in=recipient_ids,
        ).values_list("assignment_id", "student_id", "group_id")
    }
    existing = _existing_reminder_keys(
        "assignments.due_soon",
        "assignment_id",
        recipient_ids,
    )

    recipients_by_assignment = defaultdict(list)
    for enrollment in enrollments:
        for assignment in assignments_by_offering[enrollment.offering_id]:
            if assignment.collaboration_mode == Assignment.COLLABORATION_GROUP:
                group_id = group_memberships.get((assignment.id, enrollment.student_id))
                has_submitted = bool(
                    group_id and (assignment.id, group_id) in submitted_groups
                )
            else:
                has_submitted = (
                    assignment.id,
                    enrollment.student_id,
                ) in submitted_individual
            if has_submitted or (enrollment.student_id, assignment.id) in existing:
                continue
            recipients_by_assignment[assignment.id].append(enrollment.student)

    created_count = 0
    assignments_by_id = {assignment.id: assignment for assignment in assignments}
    for assignment_id, recipients in recipients_by_assignment.items():
        assignment = assignments_by_id[assignment_id]
        notify_profiles(
            recipients,
            actor=assignment.created_by,
            event_type="assignments.due_soon",
            verb=f"{assignment.title} is due within 2 hours and has not been submitted.",
            data={
                "assignment_id": assignment.id,
                "course_code": assignment.offering.course.code,
                "due_date": assignment.due_date.isoformat(),
                "activity_kind": assignment.activity_kind,
            },
            url=f"/student/assignments/{assignment.id}",
        )
        created_count += len(recipients)
    return created_count


def process_due_reminders(*, profile=None, now=None, force=False):
    if profile and not force:
        cache_key = f"due-reminders:profile:{profile.pk}"
        if not cache.add(cache_key, "1", PROFILE_THROTTLE_SECONDS):
            return {
                "library": 0,
                "assignments": 0,
                "evaluations": 0,
                "throttled": True,
            }

    return {
        "library": send_library_due_reminders(profile=profile, now=now),
        "assignments": send_assignment_due_reminders(profile=profile, now=now),
        "evaluations": send_required_evaluation_reminders(profile=profile, now=now),
        "throttled": False,
    }
