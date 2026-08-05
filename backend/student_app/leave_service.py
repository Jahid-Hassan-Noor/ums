from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from admin_app.models import ClassMeeting, Profile
from admin_app.settings_registry import setting_value
from core.common.academic_policy import (
    leave_approval_requires_sequence,
    leave_dean_approver_identifiers,
    leave_required_roles,
)
from core.common.profiles import profile_display_name
from core.media_access import protected_media_url
from notifications_package.service import notify_profile
from student_app.models import Enrollment, LeaveApproval, LeaveRequest


ACTIVE_MEETING_STATUSES = {
    ClassMeeting.STATUS_IMPORTED,
    ClassMeeting.STATUS_SCHEDULED,
}


def date_range(start_date, end_date):
    day = start_date
    while day <= end_date:
        yield day
        day += timedelta(days=1)


def enrollment_matches_meeting(enrollment, meeting):
    if meeting.tutorial_group_id and enrollment.tutorial_group_id != meeting.tutorial_group_id:
        return False
    if meeting.lab_group_id and enrollment.lab_group_id != meeting.lab_group_id:
        return False
    return True


def affected_class_meetings(student, start_date, end_date):
    enrollments = Enrollment.objects.select_related("offering").filter(
        student=student,
        completed_at__isnull=True,
    )
    affected = []
    for enrollment in enrollments:
        meetings = ClassMeeting.objects.select_related(
            "offering",
            "offering__course",
            "lecturer",
            "lecturer__user",
        ).filter(
            offering=enrollment.offering,
            status__in=ACTIVE_MEETING_STATUSES,
        )
        for meeting in meetings:
            if not enrollment_matches_meeting(enrollment, meeting):
                continue
            if meeting.meeting_date:
                if start_date <= meeting.meeting_date <= end_date:
                    affected.append(meeting)
                continue
            leave_weekdays = {day.isoweekday() for day in date_range(start_date, end_date)}
            if meeting.day_of_week in leave_weekdays:
                affected.append(meeting)
    return affected


def dean_approvers_for_student(student):
    identifiers = leave_dean_approver_identifiers()
    if not identifiers:
        return Profile.objects.none()

    scope_filter = Q()
    if student.school_id:
        scope_filter |= (
            Q(teacher_detail__school=student.school)
            | Q(teacher_detail__unit__school=student.school)
        )
    if student.center_id:
        scope_filter |= (
            Q(teacher_detail__center=student.center)
            | Q(teacher_detail__unit__center=student.center)
        )
    if not scope_filter:
        return Profile.objects.none()

    identifier_filter = Q()
    for identifier in identifiers:
        identifier_filter |= (
            Q(user__username__iexact=identifier)
            | Q(user__email__iexact=identifier)
            | Q(teacher_detail__teacher_id__iexact=identifier)
        )
    return (
        Profile.objects.select_related(
            "user", "teacher_detail"
        )
        .filter(is_active=True)
        .filter(role=Profile.ROLE_TEACHER)
        .filter(scope_filter)
        .filter(identifier_filter)
        .distinct()
        .order_by("user__first_name", "user__last_name")
    )


def teacher_for_meeting(meeting):
    return meeting.lecturer or meeting.offering.instructor


def notify_leave_profile(recipient, actor, verb, data):
    if recipient and setting_value("notifications", "notify_approvals"):
        payload = dict(data or {})
        event_type = payload.pop("event_type", "leave.updated")
        if recipient.role == Profile.ROLE_STUDENT:
            url = payload.pop("url", "/student/leave/history")
        elif recipient.role == Profile.ROLE_TEACHER:
            url = payload.pop("url", "/teacher/leave-requests")
        else:
            url = payload.pop("url", f"/{recipient.role}/notifications")
        notify_profile(
            recipient,
            actor=actor,
            event_type=event_type,
            verb=verb,
            data=payload,
            url=url,
        )


def serialize_time(value):
    return value.strftime("%H:%M") if value else None


def serialize_class_meeting(meeting):
    if not meeting:
        return None
    offering = meeting.offering
    course = offering.course if offering else None
    return {
        "id": meeting.id,
        "course_code": course.code if course else "",
        "course_title": course.title if course else "",
        "section": offering.section if offering else "",
        "class_type": meeting.class_type,
        "class_type_label": meeting.get_class_type_display(),
        "day_of_week": meeting.day_of_week,
        "day_label": meeting.get_day_of_week_display(),
        "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
        "start_time": serialize_time(meeting.start_time),
        "end_time": serialize_time(meeting.end_time),
        "topic": meeting.topic,
        "room": str(meeting.room) if meeting.room_id else "",
        "venue": str(meeting.venue) if meeting.venue_id else "",
    }


def serialize_leave_request(leave_request, viewer=None):
    approvals = list(
        leave_request.approvals.select_related(
            "approver",
            "approver__user",
            "class_meeting",
            "class_meeting__offering",
            "class_meeting__offering__course",
            "class_meeting__room",
            "class_meeting__venue",
        ).all()
    )
    pending_count = sum(1 for approval in approvals if approval.status == LeaveApproval.STATUS_PENDING)
    approved_count = sum(1 for approval in approvals if approval.status == LeaveApproval.STATUS_APPROVED)
    rejected_count = sum(1 for approval in approvals if approval.status == LeaveApproval.STATUS_REJECTED)
    return {
        "id": leave_request.id,
        "student": {
            "id": leave_request.student_id,
            "name": profile_display_name(leave_request.student),
            "student_id": leave_request.student.student_id,
        },
        "start_date": leave_request.start_date.isoformat(),
        "end_date": leave_request.end_date.isoformat(),
        "reason": leave_request.reason,
        "attachment": protected_media_url(leave_request.attachment.name) if leave_request.attachment else None,
        "status": leave_request.status,
        "review_note": leave_request.review_note,
        "created_at": leave_request.created_at.isoformat(),
        "updated_at": leave_request.updated_at.isoformat(),
        "reviewed_at": leave_request.reviewed_at.isoformat() if leave_request.reviewed_at else None,
        "approval_summary": {
            "total": len(approvals),
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
        },
        "approvals": [
            {
                "id": approval.id,
                "approver": {
                    "id": approval.approver_id,
                    "name": profile_display_name(approval.approver),
                },
                "approval_role": approval.approval_role,
                "class_meeting": serialize_class_meeting(approval.class_meeting),
                "status": approval.status,
                "note": approval.note,
                "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
                "created_at": approval.created_at.isoformat(),
                "is_current_approver": bool(viewer and approval.approver_id == viewer.id),
            }
            for approval in approvals
        ],
    }


@transaction.atomic
def submit_leave_request(student, *, start_date, end_date, reason, attachment=None):
    leave_request = LeaveRequest.objects.create(
        student=student,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        attachment=attachment,
        status=LeaveRequest.STATUS_PENDING,
    )

    approvals = []
    seen = set()
    for role in leave_required_roles():
        if role == LeaveApproval.ROLE_TEACHER:
            for meeting in affected_class_meetings(student, start_date, end_date):
                teacher = teacher_for_meeting(meeting)
                if not teacher:
                    continue
                key = (teacher.id, meeting.id, LeaveApproval.ROLE_TEACHER)
                if key in seen:
                    continue
                seen.add(key)
                approvals.append(
                    LeaveApproval(
                        leave_request=leave_request,
                        approver=teacher,
                        approval_role=LeaveApproval.ROLE_TEACHER,
                        class_meeting=meeting,
                    )
                )
        elif role == LeaveApproval.ROLE_DEAN:
            for dean in dean_approvers_for_student(student):
                key = (dean.id, None, LeaveApproval.ROLE_DEAN)
                if key in seen:
                    continue
                seen.add(key)
                approvals.append(
                    LeaveApproval(
                        leave_request=leave_request,
                        approver=dean,
                        approval_role=LeaveApproval.ROLE_DEAN,
                    )
                )

    LeaveApproval.objects.bulk_create(approvals)
    for approval in leave_request.approvals.select_related("approver"):
        notify_leave_profile(
            approval.approver,
            student,
            f"Leave approval requested by {profile_display_name(student)}",
            {
                "leave_request_id": leave_request.id,
                "approval_id": approval.id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "approval_role": approval.approval_role,
            },
        )

    if (
        not approvals
        and setting_value("workflow", "default_approval_mode")
        == "automatic_when_unassigned"
    ):
        leave_request.status = LeaveRequest.STATUS_APPROVED
        leave_request.review_note = "Approved automatically because no approvers were required."
        leave_request.reviewed_at = timezone.now()
        leave_request.save(update_fields=["status", "review_note", "reviewed_at", "updated_at"])
        notify_leave_profile(
            student,
            None,
            "Your leave of advance has been approved.",
            {"leave_request_id": leave_request.id},
        )

    return leave_request


@transaction.atomic
def decide_leave_approval(approval, *, decision, note=""):
    if decision not in {LeaveApproval.STATUS_APPROVED, LeaveApproval.STATUS_REJECTED}:
        return "Decision must be approved or rejected."

    leave_request = approval.leave_request
    if decision == LeaveApproval.STATUS_APPROVED and leave_approval_requires_sequence():
        for prior in leave_request.approvals.all().order_by("created_at", "id"):
            if prior.pk == approval.pk:
                break
            if prior.status != LeaveApproval.STATUS_APPROVED:
                return "Previous approval steps must be completed before this leave request can move forward."

    approval.status = decision
    approval.note = note
    approval.decided_at = timezone.now()
    approval.save(update_fields=["status", "note", "decided_at", "updated_at"])

    approvals = leave_request.approvals.all()
    if approvals.filter(status=LeaveApproval.STATUS_REJECTED).exists():
        leave_request.status = LeaveRequest.STATUS_REJECTED
        leave_request.reviewed_by = approval.approver
        leave_request.reviewed_at = timezone.now()
        leave_request.review_note = note
        leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
        notify_leave_profile(
            leave_request.student,
            approval.approver,
            "Your leave of advance has been rejected.",
            {"leave_request_id": leave_request.id, "note": note},
        )
        return None

    if approvals.exists() and not approvals.exclude(status=LeaveApproval.STATUS_APPROVED).exists():
        leave_request.status = LeaveRequest.STATUS_APPROVED
        leave_request.reviewed_by = approval.approver
        leave_request.reviewed_at = timezone.now()
        leave_request.review_note = "All required approvers approved this leave request."
        leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
        notify_leave_profile(
            leave_request.student,
            approval.approver,
            "Your leave of advance has been approved.",
            {"leave_request_id": leave_request.id},
        )

    return None
