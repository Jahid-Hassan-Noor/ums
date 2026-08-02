from django.db.models import Count, Q, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from admin_app import models as admin_models
from auth_app.permissions import IsExecutiveRole
from executive_app.course_schedule import (
    courses_for_scope,
    get_executive_profile,
    get_executive_scope,
    offerings_for_scope,
    schedule_rows_for_scope,
    scope_payload,
    scope_supports_academic_workflows,
    teachers_for_scope,
)
from executive_app.models import CourseOfferProposal, ResultBatch, ResultPublication
from notifications_package.models import Notification


def _status_counts(queryset, choices):
    counts = {value: 0 for value, _label in choices}
    for row in queryset.values("status").annotate(total=Count("id")):
        counts[row["status"]] = row["total"]
    return counts


def _students_for_scope(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return admin_models.Profile.objects.none()
    profile_scope = Q(**{f"student_detail__{kind}": unit}) | Q(
        **{f"student_detail__program__{kind}": unit}
    )
    return (
        admin_models.Profile.objects.filter(
            role=admin_models.Profile.ROLE_STUDENT,
            is_active=True,
        )
        .filter(profile_scope)
        .distinct()
    )


def _student_enrollment_counts(students):
    counts = {"active": 0, "inactive": 0, "graduated": 0, "other": 0}
    for row in students.values("student_detail__enrollment_status").annotate(total=Count("id")):
        key = str(row["student_detail__enrollment_status"] or "active").strip().lower()
        if key in counts:
            counts[key] += row["total"]
        else:
            counts["other"] += row["total"]
    return counts


def _scoped_academic_units(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return {"programs": 0, "academic_programs": 0, "departments": 0, "active_semesters": 0}

    programs = admin_models.Program.objects.filter(**{kind: unit}, is_active=True)
    departments = admin_models.Department.objects.filter(**{kind: unit}, is_active=True)
    return {
        "programs": programs.count(),
        "academic_programs": programs.filter(program_type=admin_models.Program.PROGRAM_ACADEMIC).count(),
        "departments": departments.count(),
        "active_semesters": admin_models.Semester.objects.filter(is_active=True).count(),
    }


def _recent_audit_logs(scope):
    if not scope.get("kind") or not scope.get("unit"):
        return []
    logs = (
        admin_models.AuditLog.objects.select_related("user__user")
        .filter(
            user__role=admin_models.Profile.ROLE_EXECUTIVE,
            details__scope__kind=scope["kind"],
            details__scope__id=scope["unit"].id,
        )
        .order_by("-created_at")[:5]
    )
    return [
        {
            "id": log.id,
            "action": log.action,
            "user": log.user.user.username if log.user_id and log.user else None,
            "timestamp": log.created_at.isoformat(),
        }
        for log in logs
    ]


def _insight_level(value, *, watch=1, risk=None):
    if risk is not None and value >= risk:
        return "risk"
    if value >= watch:
        return "watch"
    return "healthy"


def _executive_insights(*, schedule_by_status, schedule_total, result_counts, proposal_counts, unread_notifications):
    active_schedule = schedule_by_status.get("imported", 0) + schedule_by_status.get("scheduled", 0)
    cancelled_schedule = schedule_by_status.get("cancelled", 0)
    review_results = result_counts.get("review", 0)
    submitted_proposals = proposal_counts.get("submitted", 0)
    pending_notifications = unread_notifications
    return [
        {
            "key": "schedule_readiness",
            "label": "Schedule Readiness",
            "value": active_schedule,
            "total": schedule_total,
            "level": "healthy" if active_schedule or schedule_total == 0 else "watch",
            "description": "Imported or scheduled class meetings inside the assigned scope.",
            "action": "Review imported or cancelled timetable rows before term activity begins.",
        },
        {
            "key": "cancelled_schedule",
            "label": "Cancelled Schedule Load",
            "value": cancelled_schedule,
            "total": schedule_total,
            "level": _insight_level(cancelled_schedule, watch=1, risk=5),
            "description": "Class meetings cancelled inside the assigned school or centre.",
            "action": "Coordinate replacements where cancelled classes affect attendance coverage.",
        },
        {
            "key": "result_review_queue",
            "label": "Result Review Queue",
            "value": review_results,
            "total": result_counts.get("batches", 0),
            "level": _insight_level(review_results, watch=1, risk=10),
            "description": "Teacher result batches waiting for executive review.",
            "action": "Review, return, approve, or publish batches before semester close.",
        },
        {
            "key": "course_proposal_queue",
            "label": "Course Proposal Queue",
            "value": submitted_proposals,
            "total": proposal_counts.get("total", 0),
            "level": _insight_level(submitted_proposals, watch=1, risk=10),
            "description": "Course-offer proposals submitted for this executive scope.",
            "action": "Approve or reject proposals before offerings are finalized.",
        },
        {
            "key": "unread_notifications",
            "label": "Unread Workflow Signals",
            "value": pending_notifications,
            "total": pending_notifications,
            "level": _insight_level(pending_notifications, watch=1, risk=20),
            "description": "Unread notifications for this executive profile.",
            "action": "Clear operational alerts that may require a decision.",
        },
    ]


class ExecutiveStatistics(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
            scope_error = None
        except ValueError as exc:
            scope = {"kind": None, "unit": None}
            scope_error = str(exc)

        if not scope.get("kind") or not scope.get("unit"):
            scope_error = scope_error or "Executive must be assigned to one school or centre."

        academic_workflows = scope_supports_academic_workflows(scope)
        students = _students_for_scope(scope)
        teachers = teachers_for_scope(scope)
        courses = courses_for_scope(scope) if academic_workflows else admin_models.Course.objects.none()
        offerings = offerings_for_scope(scope) if academic_workflows else admin_models.CourseOffering.objects.none()
        meetings = schedule_rows_for_scope(scope) if academic_workflows else admin_models.ClassMeeting.objects.none()
        result_batches = ResultBatch.objects.filter(offering__in=offerings)
        course_proposals = CourseOfferProposal.objects.filter(course__in=courses)

        schedule_by_status = _status_counts(meetings, admin_models.ClassMeeting.STATUS_CHOICES)
        schedule_by_type = {value: 0 for value, _label in admin_models.ClassMeeting.CLASS_TYPE_CHOICES}
        for row in meetings.values("class_type").annotate(total=Count("id")):
            schedule_by_type[row["class_type"]] = row["total"]

        offering_capacity = offerings.aggregate(total=Sum("capacity"))["total"] or 0
        published_results = ResultPublication.objects.filter(offering__in=offerings).count()
        unread_notifications = (
            Notification.objects.filter(recipient=profile, unread=True).count()
            if profile
            else 0
        )
        result_status_counts = _status_counts(result_batches, ResultBatch._meta.get_field("status").choices)
        proposal_status_counts = _status_counts(course_proposals, CourseOfferProposal.STATUS_CHOICES)
        result_payload = {
            "batches": result_batches.count(),
            **result_status_counts,
            "records": result_batches.aggregate(total=Count("records"))["total"] or 0,
            "publications": published_results,
        }
        proposal_payload = {
            "total": course_proposals.count(),
            **proposal_status_counts,
        }

        data = {
            "title": "Executive Statistics",
            "section": "executive",
            "scope": scope_payload(scope),
            "scope_error": scope_error,
            "people": {
                "students": students.count(),
                "teachers": teachers.count(),
                "student_enrollment": _student_enrollment_counts(students),
            },
            "academic_units": _scoped_academic_units(scope),
            "academics": {
                "courses": courses.count(),
                "active_courses": courses.filter(is_active=True).count(),
                "offerings": offerings.count(),
                "active_offerings": offerings.filter(is_active=True).count(),
                "offering_capacity": offering_capacity,
                "active_semesters": admin_models.Semester.objects.filter(is_active=True).count(),
            },
            "schedule": {
                "meetings": meetings.count(),
                "by_status": schedule_by_status,
                "by_type": schedule_by_type,
            },
            "results": result_payload,
            "course_proposals": proposal_payload,
            "notifications": {
                "unread": unread_notifications,
            },
            "insights": _executive_insights(
                schedule_by_status=schedule_by_status,
                schedule_total=meetings.count(),
                result_counts=result_payload,
                proposal_counts=proposal_payload,
                unread_notifications=unread_notifications,
            ),
            "recent_audit_logs": _recent_audit_logs(scope),
        }
        return Response(data, status=status.HTTP_200_OK)
