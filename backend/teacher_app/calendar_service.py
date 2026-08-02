from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from admin_app.models import CourseOffering, Profile
from admin_app.schedule import (
    schedule_events_for_role,
    schedule_semester_for_role,
    serialize_schedule_event,
    serialize_schedule_semester,
)
from student_app.models import Enrollment, Exam
from student_app.registration_service import get_student_profile
from teacher_app.assignment_service import (
    get_teacher_profile,
    student_assignments,
    teacher_offerings,
)
from teacher_app.models import Assignment, CourseActivity, CourseAnnouncement


def _local_iso(value):
    return timezone.localtime(value).isoformat() if value else None


def _course_details(offering):
    if not offering:
        return {}
    return {
        "course_code": offering.course.code,
        "course_title": offering.course.title,
        "offering_id": offering.id,
    }


def _event(
    *,
    event_id,
    title,
    description,
    starts_at,
    ends_at=None,
    category="assessment",
    location="Learning portal",
    variant="default",
    event_type,
    href,
    offering=None,
):
    return {
        "id": event_id,
        "title": title,
        "description": description,
        "starts_at": _local_iso(starts_at),
        "ends_at": _local_iso(ends_at or starts_at + timedelta(minutes=30)),
        "all_day": False,
        "category": category,
        "location": location,
        "variant": variant,
        "event_type": event_type,
        "href": href,
        **_course_details(offering),
    }


def _base_schedule_events(role):
    events = []
    queryset = schedule_events_for_role(role).select_related(
        "offering",
        "offering__course",
    )
    for item in queryset:
        payload = serialize_schedule_event(item)
        metadata = item.metadata or {}
        payload.update(_course_details(item.offering))
        payload["href"] = metadata.get("href") or (
            f"/{role}/courses/{item.offering_id}"
            if item.offering_id
            else f"/{role}/timetable/weekly"
        )
        events.append(payload)
    return events


def _assignment_events(assignments, role):
    events = []
    for assignment in assignments:
        is_lab = assignment.activity_kind == Assignment.ACTIVITY_LAB
        events.append(
            _event(
                event_id=f"assignment-{assignment.id}",
                title=assignment.title,
                description=(
                    f"{assignment.get_activity_kind_display()} is due"
                ),
                starts_at=assignment.due_date,
                category="lab" if is_lab else "assessment",
                variant="success" if is_lab else "danger",
                event_type="lab_work" if is_lab else "assignment",
                href=f"/{role}/assignments/{assignment.id}",
                offering=assignment.offering,
            )
        )
    return events


def _course_activity_events(offerings, role, *, published_only):
    queryset = (
        CourseActivity.objects.select_related("offering", "offering__course")
        .filter(
            offering__in=offerings,
            assignment__isnull=True,
            activity_type=CourseActivity.TYPE_EXAM,
            due_at__isnull=False,
        )
        .order_by("due_at", "title")
    )
    if published_only:
        queryset = queryset.filter(
            Q(section__isnull=True) | Q(section__is_published=True)
        )

    return [
        _event(
            event_id=f"course-activity-{activity.id}",
            title=activity.title,
            description="Course exam or assessed class activity",
            starts_at=activity.due_at,
            ends_at=activity.closes_at,
            variant="warning",
            event_type="exam",
            href=f"/{role}/courses/{activity.offering_id}",
            offering=activity.offering,
        )
        for activity in queryset
    ]


def _exam_events(offerings, role, *, published_only):
    queryset = (
        Exam.objects.select_related("offering", "offering__course", "room")
        .prefetch_related("venue_allocations__venue__building")
        .filter(offering__in=offerings, offering__has_final_exam=True)
        .order_by("starts_at", "title")
    )
    if published_only:
        queryset = queryset.filter(is_published=True)

    events = []
    for exam in queryset:
        allocated_venues = [
            f"{allocation.venue.building.name} - {allocation.venue.name}"
            for allocation in exam.venue_allocations.all()
        ]
        location = ", ".join(allocated_venues)
        if not location and exam.room:
            location = str(exam.room)
        events.append(
            _event(
                event_id=f"exam-{exam.id}",
                title=exam.title,
                description=f"{exam.get_exam_type_display()} examination",
                starts_at=exam.starts_at,
                ends_at=exam.ends_at,
                location=location or "Venue to be confirmed",
                variant="danger",
                event_type="exam",
                href=(
                    "/student/results/exam-slip"
                    if role == Profile.ROLE_STUDENT
                    else f"/teacher/courses/{exam.offering_id}"
                ),
                offering=exam.offering,
            )
        )
    return events


def _announcement_events(offerings, role, *, published_only):
    announcement_types = [
        CourseAnnouncement.TYPE_TEST,
        CourseAnnouncement.TYPE_QUIZ,
        CourseAnnouncement.TYPE_PRESENTATION,
    ]
    queryset = (
        CourseAnnouncement.objects.select_related(
            "offering",
            "offering__course",
            "assignment",
        )
        .prefetch_related("slots")
        .filter(
            offering__in=offerings,
            announcement_type__in=announcement_types,
        )
        .order_by("scheduled_for", "title")
    )
    if published_only:
        queryset = queryset.filter(is_published=True)

    events = []
    for announcement in queryset:
        is_presentation = (
            announcement.announcement_type == CourseAnnouncement.TYPE_PRESENTATION
        )
        event_type = "presentation" if is_presentation else "exam"
        href = (
            f"/{role}/assignments/{announcement.assignment_id}"
            if announcement.assignment_id
            else f"/{role}/courses/{announcement.offering_id}"
        )
        active_slots = [slot for slot in announcement.slots.all() if slot.is_active]
        for slot in active_slots:
            events.append(
                _event(
                    event_id=f"announcement-slot-{slot.id}",
                    title=announcement.title,
                    description=slot.label or announcement.get_announcement_type_display(),
                    starts_at=slot.starts_at,
                    ends_at=slot.ends_at,
                    location=slot.label or "Course presentation",
                    variant="primary" if is_presentation else "warning",
                    event_type=event_type,
                    href=href,
                    offering=announcement.offering,
                )
            )
        if not active_slots and announcement.scheduled_for:
            events.append(
                _event(
                    event_id=f"announcement-{announcement.id}",
                    title=announcement.title,
                    description=announcement.body
                    or announcement.get_announcement_type_display(),
                    starts_at=announcement.scheduled_for,
                    location="Course activity",
                    variant="primary" if is_presentation else "warning",
                    event_type=event_type,
                    href=href,
                    offering=announcement.offering,
                )
            )
    return events


def _calendar_payload(role, title, events, user):
    events.sort(key=lambda event: (event["starts_at"], event["title"]))
    return {
        "title": title,
        "section": role,
        "schedule": {
            "events": events,
            "count": len(events),
            "semester": serialize_schedule_semester(
                schedule_semester_for_role(role, user)
            ),
        },
    }


def teacher_calendar_payload(user):
    teacher = get_teacher_profile(user)
    offerings = teacher_offerings(teacher)
    assignments = (
        Assignment.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
        )
        .filter(offering__in=offerings, due_date__isnull=False)
        .exclude(status=Assignment.STATUS_ARCHIVED)
        .order_by("due_date", "title")
    )
    events = _base_schedule_events(Profile.ROLE_TEACHER)
    events.extend(_assignment_events(assignments, Profile.ROLE_TEACHER))
    events.extend(
        _course_activity_events(
            offerings,
            Profile.ROLE_TEACHER,
            published_only=False,
        )
    )
    events.extend(
        _exam_events(
            offerings,
            Profile.ROLE_TEACHER,
            published_only=False,
        )
    )
    events.extend(
        _announcement_events(
            offerings,
            Profile.ROLE_TEACHER,
            published_only=False,
        )
    )
    return _calendar_payload(Profile.ROLE_TEACHER, "Calendar", events, user)


def student_calendar_payload(user):
    student = get_student_profile(user)
    offering_ids = Enrollment.objects.filter(
        student=student,
        completed_at__isnull=True,
    ).values("offering_id")
    offerings = CourseOffering.objects.select_related(
        "course",
        "semester",
    ).filter(pk__in=offering_ids, is_active=True)

    assignments = (
        student_assignments(student)
        .filter(due_date__isnull=False)
        .exclude(status=Assignment.STATUS_ARCHIVED)
    )
    events = _base_schedule_events(Profile.ROLE_STUDENT)
    events.extend(_assignment_events(assignments, Profile.ROLE_STUDENT))
    events.extend(
        _course_activity_events(
            offerings,
            Profile.ROLE_STUDENT,
            published_only=True,
        )
    )
    events.extend(
        _exam_events(
            offerings,
            Profile.ROLE_STUDENT,
            published_only=True,
        )
    )
    events.extend(
        _announcement_events(
            offerings,
            Profile.ROLE_STUDENT,
            published_only=True,
        )
    )
    return _calendar_payload(Profile.ROLE_STUDENT, "Calendar", events, user)
