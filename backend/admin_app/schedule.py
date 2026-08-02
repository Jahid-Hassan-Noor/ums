from datetime import date, timedelta
from types import SimpleNamespace

from django.db.models import Q
from django.utils import timezone

from admin_app.models import AcademicEvent, CourseOffering, Profile, Semester
from student_app.models import Enrollment, Exam


SCHEDULE_LOCATION_KEY = "location"
SCHEDULE_CATEGORY_KEY = "category"
SCHEDULE_VARIANT_KEY = "variant"
SCHEDULE_AUDIENCES_KEY = "schedule_audiences"


def schedule_events_for_role(role):
    return AcademicEvent.objects.filter(
        Q(metadata__contains={SCHEDULE_AUDIENCES_KEY: [role]})
        | Q(metadata__audience_role=role)
    ).order_by("starts_at", "title")


def serialize_schedule_event(event):
    metadata = event.metadata or {}
    ends_at = event.ends_at or event.starts_at + timedelta(hours=1)

    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "starts_at": timezone.localtime(event.starts_at).isoformat(),
        "ends_at": timezone.localtime(ends_at).isoformat(),
        "all_day": event.all_day,
        "category": metadata.get(SCHEDULE_CATEGORY_KEY, event.event_type),
        "location": metadata.get(SCHEDULE_LOCATION_KEY, ""),
        "variant": metadata.get(SCHEDULE_VARIANT_KEY, "default"),
        "event_type": event.event_type,
    }


def serialize_schedule_semester(semester):
    if not semester:
        return None
    return {
        "id": semester.id,
        "name": semester.name,
        "start_date": semester.start_date.isoformat() if semester.start_date else None,
        "end_date": semester.end_date.isoformat() if semester.end_date else None,
        "starting_week": semester.starting_week,
    }


def reference_semester_for_date(calendar_group, on_date=None):
    if calendar_group != Semester.CALENDAR_UNDERGRADUATE:
        return None

    from admin_app.views.admin_semesters import UGP_2025_2026_REFERENCE

    on_date = on_date or timezone.localdate()
    for index, reference in enumerate(UGP_2025_2026_REFERENCE, start=1):
        start_date = date.fromisoformat(reference["start_date"])
        end_date = date.fromisoformat(reference["end_date"])
        if start_date <= on_date <= end_date:
            return SimpleNamespace(
                id=-index,
                name=reference["name"],
                start_date=start_date,
                end_date=end_date,
                starting_week=1,
            )
    return None


def schedule_semester_for_role(role, user=None):
    if not user or not user.is_authenticated:
        return None

    if role == Profile.ROLE_STUDENT:
        from student_app.registration_service import (
            active_semester,
            calendar_group_for_student,
            get_student_profile,
        )

        student = get_student_profile(user)
        semester = active_semester(student=student)
        if semester:
            return semester
        calendar_group = calendar_group_for_student(student) if student else None
        dated_semester = (
            Semester.objects.filter(
                calendar_group=calendar_group,
                start_date__lte=timezone.localdate(),
                end_date__gte=timezone.localdate(),
            )
            .order_by("-start_date", "-created_at")
            .first()
            if calendar_group
            else None
        )
        return dated_semester or reference_semester_for_date(calendar_group)

    if role == Profile.ROLE_TEACHER:
        profile = (
            Profile.objects.filter(
                user=user,
                role=Profile.ROLE_TEACHER,
                is_active=True,
            )
            .first()
        )
        if not profile:
            return None
        offering = (
            CourseOffering.objects.select_related("semester")
            .filter(
                Q(instructor=profile) | Q(class_meetings__lecturer=profile),
                semester__is_active=True,
            )
            .order_by("-semester__start_date", "-semester__created_at")
            .first()
        )
        if offering:
            return offering.semester
        dated_semester = (
            Semester.objects.filter(
                start_date__lte=timezone.localdate(),
                end_date__gte=timezone.localdate(),
            )
            .order_by("-is_active", "-start_date", "-created_at")
            .first()
        )
        return dated_semester or reference_semester_for_date(
            Semester.CALENDAR_UNDERGRADUATE
        )

    return None


def final_exam_events_for_student(user):
    profile = (
        Profile.objects.filter(
            user=user,
            role=Profile.ROLE_STUDENT,
            is_active=True,
        )
        .first()
        if user and user.is_authenticated
        else None
    )
    if not profile:
        return []

    offering_ids = Enrollment.objects.filter(student=profile).values("offering_id")
    exams = (
        Exam.objects.select_related("offering", "offering__course", "semester")
        .prefetch_related("venue_allocations__venue__building")
        .filter(
            offering_id__in=offering_ids,
            exam_type=Exam.TYPE_FINAL,
            is_published=True,
        )
        .order_by("starts_at", "offering__course__code")
    )
    events = []
    for exam in exams:
        offering = exam.offering
        locations = [
            f"{allocation.venue.building.name} - {allocation.venue.name}"
            for allocation in exam.venue_allocations.all()
        ]
        events.append(
            {
                "id": f"final-exam-{exam.id}",
                "title": f"{offering.course.code} Final Examination",
                "description": (
                    f"{offering.course.title}"
                    + (f" (Section {offering.section})" if offering.section else "")
                ),
                "starts_at": timezone.localtime(exam.starts_at).isoformat(),
                "ends_at": (
                    timezone.localtime(exam.ends_at).isoformat()
                    if exam.ends_at
                    else timezone.localtime(exam.starts_at + timedelta(hours=1)).isoformat()
                ),
                "all_day": False,
                "category": "assessment",
                "location": ", ".join(locations) or "Venue to be confirmed",
                "variant": "danger",
                "event_type": "final_exam",
            }
        )
    return events


def schedule_payload_for_role(role, title, section, user=None):
    events = [serialize_schedule_event(event) for event in schedule_events_for_role(role)]
    if role == Profile.ROLE_STUDENT:
        events.extend(final_exam_events_for_student(user))
        events.sort(key=lambda event: (event["starts_at"], event["title"]))

    return {
        "title": title,
        "section": section,
        "schedule": {
            "events": events,
            "count": len(events),
            "semester": serialize_schedule_semester(
                schedule_semester_for_role(role, user)
            ),
        },
    }
