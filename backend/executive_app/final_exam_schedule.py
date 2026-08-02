from datetime import datetime

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from admin_app import models as admin_models
from technician_app.venue_booking_service import booking_conflict_message
from student_app import models as student_models


class FinalExamScheduleError(Exception):
    def __init__(self, detail, *, status_code=400, conflicts=None):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.conflicts = conflicts or []


def _profile_name(profile):
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _course_label(offering):
    section = f" {offering.section}" if offering.section else ""
    return f"{offering.course.code}{section}"


def _aware_datetime(value_date, value_time):
    return timezone.make_aware(
        datetime.combine(value_date, value_time),
        timezone.get_current_timezone(),
    )


def final_exam_edit_window_error(semester):
    today = timezone.localdate()
    if not semester.start_date:
        return "Admin must define the semester start date before final exams can be scheduled."
    if today < semester.start_date:
        return f"Final exam scheduling opens when the semester starts on {semester.start_date.isoformat()}."
    if not semester.examination_starts_on or not semester.examination_ends_on:
        return "Admin must define the final examination period before executives can schedule exams."
    if today >= semester.examination_starts_on:
        return (
            "Final exam schedules are locked because the examination period started on "
            f"{semester.examination_starts_on.isoformat()}."
        )
    return None


def final_exam_options(offerings):
    offerings = list(
        offerings.select_related("course", "semester").filter(is_active=True, has_final_exam=True).order_by(
            "semester__examination_starts_on",
            "course__code",
            "section",
        )
    )
    counts = {
        row["offering_id"]: row["count"]
        for row in student_models.Enrollment.objects.filter(
            offering_id__in=[offering.id for offering in offerings]
        )
        .values("offering_id")
        .annotate(count=Count("id"))
    }
    return [
        {
            "id": offering.id,
            "course": {
                "id": offering.course_id,
                "code": offering.course.code,
                "title": offering.course.title,
            },
            "section": offering.section,
            "semester": {
                "id": offering.semester_id,
                "name": offering.semester.name,
                "academic_session": offering.semester.academic_session,
                "start_date": (
                    offering.semester.start_date.isoformat()
                    if offering.semester.start_date
                    else None
                ),
                "examination_starts_on": (
                    offering.semester.examination_starts_on.isoformat()
                    if offering.semester.examination_starts_on
                    else None
                ),
                "examination_ends_on": (
                    offering.semester.examination_ends_on.isoformat()
                    if offering.semester.examination_ends_on
                    else None
                ),
            },
            "enrollment_count": counts.get(offering.id, 0),
            "edit_window_error": final_exam_edit_window_error(offering.semester),
        }
        for offering in offerings
    ]


def final_exams_for_offerings(offerings):
    return (
        student_models.Exam.objects.select_related(
            "offering",
            "offering__course",
            "semester",
        )
        .prefetch_related("venue_allocations__venue__building")
        .filter(
            exam_type=student_models.Exam.TYPE_FINAL,
            offering__in=offerings,
            offering__has_final_exam=True,
        )
        .order_by("starts_at", "offering__course__code", "offering__section")
    )


def serialize_final_exam(exam):
    offering = exam.offering
    allocations = list(exam.venue_allocations.all())
    return {
        "id": exam.id,
        "offering_id": exam.offering_id,
        "course": {
            "id": offering.course_id,
            "code": offering.course.code,
            "title": offering.course.title,
        },
        "section": offering.section,
        "semester": {
            "id": exam.semester_id,
            "name": exam.semester.name,
            "academic_session": exam.semester.academic_session,
            "examination_starts_on": (
                exam.semester.examination_starts_on.isoformat()
                if exam.semester.examination_starts_on
                else None
            ),
            "examination_ends_on": (
                exam.semester.examination_ends_on.isoformat()
                if exam.semester.examination_ends_on
                else None
            ),
        },
        "title": exam.title,
        "exam_date": timezone.localtime(exam.starts_at).date().isoformat(),
        "start_time": timezone.localtime(exam.starts_at).strftime("%H:%M"),
        "end_time": (
            timezone.localtime(exam.ends_at).strftime("%H:%M")
            if exam.ends_at
            else ""
        ),
        "instructions": exam.instructions,
        "is_published": exam.is_published,
        "enrollment_count": student_models.Enrollment.objects.filter(
            offering_id=exam.offering_id
        ).count(),
        "venue_allocations": [
            {
                "id": allocation.id,
                "venue_id": allocation.venue_id,
                "seats": allocation.seats,
                "venue": {
                    "id": allocation.venue_id,
                    "code": allocation.venue.code,
                    "name": allocation.venue.name,
                    "capacity": allocation.venue.capacity,
                    "building": allocation.venue.building.name,
                },
            }
            for allocation in allocations
        ],
        "edit_window_error": final_exam_edit_window_error(exam.semester),
    }


def _parse_exam_time(payload, semester):
    exam_date = parse_date(str(payload.get("exam_date") or ""))
    start_time = parse_time(str(payload.get("start_time") or ""))
    end_time = parse_time(str(payload.get("end_time") or ""))
    if not exam_date:
        raise FinalExamScheduleError("Select a valid final exam date.")
    if not start_time or not end_time:
        raise FinalExamScheduleError("Select a valid final exam start and end time.")
    if start_time >= end_time:
        raise FinalExamScheduleError("Final exam end time must be after its start time.")
    if not semester.examination_starts_on or not semester.examination_ends_on:
        raise FinalExamScheduleError(
            "Admin must define the final examination period before executives can schedule exams."
        )
    if not semester.examination_starts_on <= exam_date <= semester.examination_ends_on:
        raise FinalExamScheduleError(
            "Final exams must be scheduled inside the admin-defined examination period "
            f"({semester.examination_starts_on.isoformat()} to {semester.examination_ends_on.isoformat()})."
        )
    return (
        exam_date,
        start_time,
        end_time,
        _aware_datetime(exam_date, start_time),
        _aware_datetime(exam_date, end_time),
    )


def _parse_allocations(payload, enrollment_count):
    raw_allocations = payload.get("venue_allocations")
    if not isinstance(raw_allocations, list) or not raw_allocations:
        raise FinalExamScheduleError("Select at least one venue for the final exam.")

    parsed = []
    seen_venue_ids = set()
    for index, raw_allocation in enumerate(raw_allocations, start=1):
        if not isinstance(raw_allocation, dict):
            raise FinalExamScheduleError(f"Venue allocation #{index} is invalid.")
        try:
            venue_id = int(raw_allocation.get("venue_id"))
        except (TypeError, ValueError):
            raise FinalExamScheduleError(f"Venue allocation #{index} must select a venue.")
        if venue_id in seen_venue_ids:
            raise FinalExamScheduleError("The same venue cannot be allocated twice to one final exam.")
        seen_venue_ids.add(venue_id)
        try:
            seats = int(raw_allocation.get("seats"))
        except (TypeError, ValueError):
            seats = enrollment_count if len(raw_allocations) == 1 and enrollment_count else 0
        if seats < 1:
            raise FinalExamScheduleError(
                f"Venue allocation #{index} must reserve at least one seat."
            )
        parsed.append({"venue_id": venue_id, "seats": seats})

    venues = {
        venue.id: venue
        for venue in admin_models.Venue.objects.select_related("building").filter(
            pk__in=seen_venue_ids,
            is_active=True,
        )
    }
    if len(venues) != len(seen_venue_ids):
        raise FinalExamScheduleError("One or more selected venues are unavailable.")
    for allocation in parsed:
        venue = venues[allocation["venue_id"]]
        if not venue.capacity:
            raise FinalExamScheduleError(
                f"Admin must define a capacity for {venue.name} before it can host a final exam."
            )
        if allocation["seats"] > venue.capacity:
            raise FinalExamScheduleError(
                f"{venue.name} has capacity {venue.capacity}, but this exam reserves {allocation['seats']} seats."
            )
        allocation["venue"] = venue

    reserved_seats = sum(allocation["seats"] for allocation in parsed)
    if reserved_seats < enrollment_count:
        raise FinalExamScheduleError(
            f"This course has {enrollment_count} enrolled students, but only {reserved_seats} exam seats are reserved."
        )
    return parsed


def _student_conflicts(offering, starts_at, ends_at, exclude_exam_id=None):
    student_ids = list(
        student_models.Enrollment.objects.filter(offering=offering).values_list(
            "student_id",
            flat=True,
        )
    )
    if not student_ids:
        return []

    exams = (
        student_models.Exam.objects.select_related("offering", "offering__course")
        .filter(
            semester=offering.semester,
            exam_type=student_models.Exam.TYPE_FINAL,
            offering__has_final_exam=True,
            starts_at__lt=ends_at,
            ends_at__gt=starts_at,
            offering__isnull=False,
        )
        .exclude(pk=exclude_exam_id)
    )
    conflicts = []
    for exam in exams:
        overlapping_students = list(
            student_models.Enrollment.objects.select_related(
                "student",
                "student__user",
                "student__student_detail",
            )
            .filter(offering=exam.offering, student_id__in=student_ids)
            .order_by("student__user__first_name", "student__user__last_name")[:6]
        )
        if not overlapping_students:
            continue
        total = student_models.Enrollment.objects.filter(
            offering=exam.offering,
            student_id__in=student_ids,
        ).count()
        conflicts.append(
            {
                "exam_id": exam.id,
                "course": _course_label(exam.offering),
                "students": [
                    {
                        "id": enrollment.student_id,
                        "name": _profile_name(enrollment.student),
                        "student_id": enrollment.student.student_id,
                    }
                    for enrollment in overlapping_students
                ],
                "student_count": total,
            }
        )
    return conflicts


def _venue_capacity_conflicts(allocations, starts_at, ends_at, exclude_exam_id=None):
    conflicts = []
    for allocation in allocations:
        venue = allocation["venue"]
        overlapping = (
            student_models.ExamVenueAllocation.objects.select_related(
                "exam",
                "exam__offering",
                "exam__offering__course",
            )
            .filter(
                venue=venue,
                exam__exam_type=student_models.Exam.TYPE_FINAL,
                exam__offering__has_final_exam=True,
                exam__starts_at__lt=ends_at,
                exam__ends_at__gt=starts_at,
            )
            .exclude(exam_id=exclude_exam_id)
        )
        occupied = sum(candidate.seats for candidate in overlapping)
        requested = allocation["seats"]
        if occupied + requested <= venue.capacity:
            continue
        conflicts.append(
            {
                "venue_id": venue.id,
                "venue": venue.name,
                "capacity": venue.capacity,
                "already_reserved": occupied,
                "requested": requested,
                "exams": [
                    {
                        "exam_id": candidate.exam_id,
                        "course": _course_label(candidate.exam.offering),
                        "seats": candidate.seats,
                    }
                    for candidate in overlapping
                ],
            }
        )
    return conflicts


@transaction.atomic
def save_final_exam(*, offerings, payload):
    try:
        offering_id = int(payload.get("offering_id"))
    except (TypeError, ValueError):
        raise FinalExamScheduleError("Select a course offering for the final exam.")

    offering = (
        offerings.select_related("course", "semester").filter(pk=offering_id, is_active=True).first()
    )
    if not offering:
        raise FinalExamScheduleError("Course offering not found in your executive scope.", status_code=404)
    if not offering.has_final_exam:
        raise FinalExamScheduleError(
            "This course offering is marked as coursework-only and does not require a final exam.",
            status_code=409,
        )

    window_error = final_exam_edit_window_error(offering.semester)
    if window_error:
        raise FinalExamScheduleError(window_error, status_code=409)

    exam_id = payload.get("exam_id")
    exam = None
    if exam_id:
        exam = (
            student_models.Exam.objects.select_for_update()
            .filter(
                pk=exam_id,
                exam_type=student_models.Exam.TYPE_FINAL,
                offering__in=offerings,
            )
            .first()
        )
        if not exam:
            raise FinalExamScheduleError("Final exam schedule not found.", status_code=404)
        existing_window_error = final_exam_edit_window_error(exam.semester)
        if existing_window_error:
            raise FinalExamScheduleError(existing_window_error, status_code=409)

    duplicate = student_models.Exam.objects.filter(
        offering=offering,
        exam_type=student_models.Exam.TYPE_FINAL,
    )
    if exam:
        duplicate = duplicate.exclude(pk=exam.pk)
    if duplicate.exists():
        raise FinalExamScheduleError(
            f"{_course_label(offering)} already has a final exam schedule.",
            status_code=409,
        )

    exam_date, start_time, end_time, starts_at, ends_at = _parse_exam_time(
        payload,
        offering.semester,
    )
    enrollment_count = student_models.Enrollment.objects.filter(offering=offering).count()
    allocations = _parse_allocations(payload, enrollment_count)
    list(
        admin_models.Venue.objects.select_for_update()
        .filter(pk__in=[allocation["venue_id"] for allocation in allocations])
        .values_list("id", flat=True)
    )

    student_conflicts = _student_conflicts(
        offering,
        starts_at,
        ends_at,
        exclude_exam_id=exam.id if exam else None,
    )
    if student_conflicts:
        first = student_conflicts[0]
        names = ", ".join(student["name"] for student in first["students"])
        remaining = first["student_count"] - len(first["students"])
        if remaining > 0:
            names += f", and {remaining} more"
        raise FinalExamScheduleError(
            f"{first['student_count']} student(s) also take {first['course']}, whose final exam overlaps this time: {names}.",
            status_code=409,
            conflicts=student_conflicts,
        )

    for allocation in allocations:
        ordinary_conflict = booking_conflict_message(
            allocation["venue"],
            exam_date,
            start_time,
            end_time,
            include_final_exams=False,
            include_recurring_classes=False,
        )
        if ordinary_conflict:
            raise FinalExamScheduleError(ordinary_conflict, status_code=409)

    capacity_conflicts = _venue_capacity_conflicts(
        allocations,
        starts_at,
        ends_at,
        exclude_exam_id=exam.id if exam else None,
    )
    if capacity_conflicts:
        first = capacity_conflicts[0]
        raise FinalExamScheduleError(
            f"{first['venue']} capacity is {first['capacity']}; {first['already_reserved']} seats are already reserved and this exam requests {first['requested']} more.",
            status_code=409,
            conflicts=capacity_conflicts,
        )

    if not exam:
        exam = student_models.Exam(exam_type=student_models.Exam.TYPE_FINAL)
    exam.offering = offering
    exam.semester = offering.semester
    exam.title = f"{_course_label(offering)} Final Examination"
    exam.starts_at = starts_at
    exam.ends_at = ends_at
    exam.instructions = str(payload.get("instructions") or "").strip()
    exam.is_published = True
    exam.save()
    exam.venue_allocations.all().delete()
    student_models.ExamVenueAllocation.objects.bulk_create(
        [
            student_models.ExamVenueAllocation(
                exam=exam,
                venue=allocation["venue"],
                seats=allocation["seats"],
            )
            for allocation in allocations
        ]
    )
    return (
        student_models.Exam.objects.select_related(
            "offering",
            "offering__course",
            "semester",
        )
        .prefetch_related("venue_allocations__venue__building")
        .get(pk=exam.pk)
    )


@transaction.atomic
def delete_final_exam(*, offerings, exam_id):
    exam = (
        student_models.Exam.objects.select_for_update()
        .select_related("semester", "offering", "offering__course")
        .filter(
            pk=exam_id,
            exam_type=student_models.Exam.TYPE_FINAL,
            offering__in=offerings,
        )
        .first()
    )
    if not exam:
        raise FinalExamScheduleError("Final exam schedule not found.", status_code=404)
    window_error = final_exam_edit_window_error(exam.semester)
    if window_error:
        raise FinalExamScheduleError(window_error, status_code=409)
    exam.delete()


def final_exam_venue_conflict_message(venue, booking_date, start_time, end_time):
    starts_at = _aware_datetime(booking_date, start_time)
    ends_at = _aware_datetime(booking_date, end_time)
    allocation = (
        student_models.ExamVenueAllocation.objects.select_related(
            "exam",
            "exam__offering",
            "exam__offering__course",
        )
        .filter(
            venue=venue,
            exam__exam_type=student_models.Exam.TYPE_FINAL,
            exam__offering__has_final_exam=True,
            exam__starts_at__lt=ends_at,
            exam__ends_at__gt=starts_at,
        )
        .order_by("exam__starts_at")
        .first()
    )
    if not allocation:
        return None
    exam = allocation.exam
    return (
        f"{venue.name} is assigned to final exam {_course_label(exam.offering)} "
        f"from {timezone.localtime(exam.starts_at).strftime('%H:%M')} "
        f"to {timezone.localtime(exam.ends_at).strftime('%H:%M')}."
    )
