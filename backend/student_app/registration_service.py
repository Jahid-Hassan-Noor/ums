from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status

from admin_app import models as admin_models
from core.common.academic_policy import (
    evaluation_activity_label,
    registration_credit_policy,
    registration_passed_course_retake_allowed,
    registration_prerequisites_required,
)
from core.common.profiles import (
    get_student_profile,
    profile_display_name,
)
from executive_app.evaluation_service import registration_evaluation_gate
from student_app import models as student_models


ACTIVE_REGISTRATION_STATUSES = {
    student_models.CourseRegistration.STATUS_PENDING,
    student_models.CourseRegistration.STATUS_APPROVED,
}

ACTIVE_MEETING_STATUSES = {
    admin_models.ClassMeeting.STATUS_IMPORTED,
    admin_models.ClassMeeting.STATUS_SCHEDULED,
}

FAIL_GRADES = {"C-", "D+", "D", "F"}
MINIMUM_PASSING_GRADE_POINTS = Decimal("2.00")
MINIMUM_PASSING_SCORE = Decimal("50.00")


def calendar_group_for_center(center):
    if not center or not center.is_academic_center():
        return None
    if center.uses_semester_calendar():
        return center.effective_semester_calendar_group()
    return None


def calendar_group_for_program(program):
    if not program:
        return None
    center_group = calendar_group_for_center(getattr(program, "center", None))
    if center_group or getattr(program, "center_id", None):
        return center_group
    if getattr(program, "school_id", None):
        return admin_models.Semester.CALENDAR_UNDERGRADUATE
    return None


def calendar_group_for_student(student):
    center_group = calendar_group_for_center(getattr(student, "center", None))
    if center_group or getattr(student, "center_id", None):
        return center_group

    program_group = calendar_group_for_program(getattr(student, "program", None))
    if program_group or getattr(student, "program_id", None):
        return program_group

    department = getattr(student, "department", None)
    center_group = calendar_group_for_center(getattr(department, "center", None))
    if center_group or getattr(department, "center_id", None):
        return center_group
    if getattr(department, "school_id", None):
        return admin_models.Semester.CALENDAR_UNDERGRADUATE

    if getattr(student, "school_id", None):
        return admin_models.Semester.CALENDAR_UNDERGRADUATE
    return admin_models.Semester.CALENDAR_UNDERGRADUATE


def active_semester(semester_id=None, now=None, student=None, prefer_registration=False):
    now = now or timezone.now()
    semesters = admin_models.Semester.objects.all()
    if student is not None:
        calendar_group = calendar_group_for_student(student)
        if not calendar_group:
            return None
        semesters = semesters.filter(calendar_group=calendar_group)
    if semester_id:
        semesters = semesters.filter(pk=semester_id)
    if prefer_registration:
        registration_semester = (
            semesters.filter(
                registrationperiod__is_active=True,
                registrationperiod__opens_at__lte=now,
                registrationperiod__closes_at__gte=now,
            )
            .order_by("registrationperiod__opens_at", "-start_date", "-created_at")
            .first()
        )
        if registration_semester:
            return registration_semester
    return semesters.filter(is_active=True).order_by("-start_date", "-created_at").first()


def active_registration_period(semester, now=None):
    if not semester:
        return None
    now = now or timezone.now()
    return (
        student_models.RegistrationPeriod.objects.filter(
            semester=semester,
            is_active=True,
            opens_at__lte=now,
            closes_at__gte=now,
        )
        .order_by("opens_at")
        .first()
    )


def student_offerings(student, semester=None):
    qs = (
        admin_models.CourseOffering.objects.select_related(
            "course",
            "semester",
            "instructor",
            "instructor__user",
        )
        .prefetch_related(
            "course__prerequisites",
            "eligible_schools",
            "eligible_centers",
            "tutorial_groups__lab_groups",
        )
        .filter(is_active=True)
        .order_by("course__code", "section")
    )
    if semester:
        qs = qs.filter(semester=semester)

    scope = Q()
    if student.program_id:
        scope |= Q(course__program=student.program)
    student_school = getattr(student, "school", None) or getattr(getattr(student, "program", None), "school", None)
    student_center = getattr(student, "center", None) or getattr(getattr(student, "program", None), "center", None)
    if student_school:
        scope |= (
            Q(course__school=student_school)
            | Q(course__program__school=student_school)
            | Q(eligible_schools=student_school)
        )
    if student_center:
        scope |= (
            Q(course__center=student_center)
            | Q(course__program__center=student_center)
            | Q(eligible_centers=student_center)
        )
    if not scope:
        return qs.none()
    return qs.filter(scope).distinct()


def current_credit_hours(student, semester, exclude_offering=None):
    qs = student_models.CourseRegistration.objects.filter(
        student=student,
        offering__semester=semester,
        status__in=ACTIVE_REGISTRATION_STATUSES,
    )
    if exclude_offering:
        qs = qs.exclude(offering=exclude_offering)
    return qs.aggregate(total=Sum("offering__course__credits"))["total"] or 0



def tutorial_group_seats(group, exclude_registration=None):
    count_qs = student_models.CourseRegistration.objects.filter(
        tutorial_group=group,
        status__in=ACTIVE_REGISTRATION_STATUSES,
    )
    if exclude_registration:
        count_qs = count_qs.exclude(pk=exclude_registration.pk)
    used = count_qs.count()
    return {
        "capacity": group.capacity,
        "used": used,
        "remaining": max(group.capacity - used, 0),
    }


def lab_group_seats(group, exclude_registration=None):
    count_qs = student_models.CourseRegistration.objects.filter(
        lab_group=group,
        status__in=ACTIVE_REGISTRATION_STATUSES,
    )
    if exclude_registration:
        count_qs = count_qs.exclude(pk=exclude_registration.pk)
    used = count_qs.count()
    return {
        "capacity": group.capacity,
        "used": used,
        "remaining": max(group.capacity - used, 0),
    }


def offering_seats(offering, exclude_registration=None):
    count_qs = student_models.CourseRegistration.objects.filter(
        offering=offering,
        status__in=ACTIVE_REGISTRATION_STATUSES,
    )
    if exclude_registration:
        count_qs = count_qs.exclude(pk=exclude_registration.pk)
    used = count_qs.count()
    return {
        "capacity": offering.capacity,
        "used": used,
        "remaining": max(offering.capacity - used, 0),
    }


def serialize_group_options(offering):
    groups = []
    for tutorial_group in offering.tutorial_groups.all():
        if not tutorial_group.is_active:
            continue
        tutorial_seats = tutorial_group_seats(tutorial_group)
        groups.append(
            {
                "id": tutorial_group.id,
                "code": tutorial_group.code,
                "capacity": tutorial_group.capacity,
                "used": tutorial_seats["used"],
                "remaining": tutorial_seats["remaining"],
                "lab_groups": [
                    {
                        "id": lab_group.id,
                        "code": lab_group.code,
                        "capacity": lab_group.capacity,
                        "used": lab_group_seats(lab_group)["used"],
                        "remaining": lab_group_seats(lab_group)["remaining"],
                    }
                    for lab_group in tutorial_group.lab_groups.all()
                    if lab_group.is_active
                ],
            }
        )
    return groups


def serialize_offering_for_registration(offering, student=None):
    seats = offering_seats(offering)
    credit_policy = registration_credit_policy(student=student, semester=offering.semester)
    return {
        "id": offering.id,
        "course": {
            "id": offering.course_id,
            "code": offering.course.code,
            "title": offering.course.title,
            "credits": offering.course.credits,
            "has_lab": offering.course.has_lab,
            "prerequisites": [
                {
                    "id": prerequisite.id,
                    "code": prerequisite.code,
                    "title": prerequisite.title,
                }
                for prerequisite in offering.course.prerequisites.order_by("code")
            ],
        },
        "semester": {
            "id": offering.semester_id,
            "name": offering.semester.name,
            "semester_type": offering.semester.semester_type,
            "max_credit_hours": offering.semester.max_credit_hours,
        },
        "registration_policy": credit_policy,
        "section": offering.section,
        "capacity": offering.capacity,
        "used": seats["used"],
        "remaining": seats["remaining"],
        "groups": serialize_group_options(offering),
    }


def _group_by_id_or_code(qs, group_id=None, group_code=None):
    if group_id:
        return qs.filter(pk=group_id).first()
    if group_code:
        return qs.filter(code__iexact=str(group_code).strip()).first()
    return qs.first()


def resolve_group_selection(
    offering,
    *,
    tutorial_group_id=None,
    tutorial_group_code=None,
    lab_group_id=None,
    lab_group_code=None,
):
    tutorials = offering.tutorial_groups.filter(is_active=True).order_by("code")
    tutorial_group = _group_by_id_or_code(tutorials, tutorial_group_id, tutorial_group_code)
    if tutorials.exists() and not tutorial_group:
        return None, None, "Select a valid tutorial group for this course."
    if not tutorials.exists():
        tutorial_group = None

    lab_group = None
    if offering.course.has_lab:
        if not tutorial_group:
            return None, None, "Courses with lab classes require a tutorial group before lab groups can be selected."
        labs = tutorial_group.lab_groups.filter(is_active=True).order_by("code")
        lab_group = _group_by_id_or_code(labs, lab_group_id, lab_group_code)
        if not lab_group:
            return None, None, "Select a valid lab group for this course."
    elif lab_group_id or lab_group_code:
        return None, None, "Lab groups can only be selected for courses that have lab classes."

    return tutorial_group, lab_group, None


def ensure_group_capacity(tutorial_group, lab_group, *, exclude_registration=None):
    if tutorial_group:
        seats = tutorial_group_seats(tutorial_group, exclude_registration=exclude_registration)
        if seats["remaining"] <= 0:
            return f"Tutorial group {tutorial_group.code} is already full."
    if lab_group:
        seats = lab_group_seats(lab_group, exclude_registration=exclude_registration)
        if seats["remaining"] <= 0:
            return f"Lab group {lab_group.code} is already full."
    return None


def ensure_offering_capacity(offering, *, exclude_registration=None):
    if offering.tutorial_groups.filter(is_active=True).exists():
        return None
    seats = offering_seats(offering, exclude_registration=exclude_registration)
    if seats["capacity"] and seats["remaining"] <= 0:
        return "This course offering is already full."
    return None


def missing_prerequisites(student, course):
    prerequisite_ids = set(course.prerequisites.values_list("id", flat=True))
    if not prerequisite_ids:
        return []

    completed_ids = set(
        student_models.Enrollment.objects.filter(
            student=student,
            offering__course_id__in=prerequisite_ids,
            completed_at__isnull=False,
        ).values_list("offering__course_id", flat=True)
    )
    return list(course.prerequisites.exclude(pk__in=completed_ids).order_by("code"))


def transcript_record_is_pass(record):
    grade = str(record.grade or "").strip().upper()
    if grade in FAIL_GRADES:
        return False
    if record.grade_points is not None:
        return record.grade_points >= MINIMUM_PASSING_GRADE_POINTS
    if record.score is not None:
        return record.score >= MINIMUM_PASSING_SCORE
    return bool(grade)


def passed_course_record(student, course, semester):
    records = (
        student_models.TranscriptRecord.objects.filter(
            student=student,
            published_at__isnull=False,
        )
        .filter(Q(offering__course=course) | Q(course_code__iexact=course.code))
        .exclude(semester=semester)
        .order_by("-published_at", "-created_at")
    )
    return next((record for record in records if transcript_record_is_pass(record)), None)


def meeting_matches_groups(meeting, tutorial_group, lab_group):
    if meeting.tutorial_group_id and meeting.tutorial_group_id != getattr(tutorial_group, "id", None):
        return False
    if meeting.lab_group_id and meeting.lab_group_id != getattr(lab_group, "id", None):
        return False
    return True


def selected_class_meetings(offering, tutorial_group, lab_group):
    meetings = (
        admin_models.ClassMeeting.objects.filter(
            offering=offering,
            status__in=ACTIVE_MEETING_STATUSES,
        )
        .select_related("offering", "offering__course", "tutorial_group", "lab_group")
        .order_by("meeting_date", "day_of_week", "start_time")
    )
    return [
        meeting
        for meeting in meetings
        if meeting_matches_groups(meeting, tutorial_group, lab_group)
    ]


def meetings_overlap(first, second):
    if first.meeting_date and second.meeting_date:
        same_occurrence = first.meeting_date == second.meeting_date
    else:
        same_occurrence = first.day_of_week == second.day_of_week
    return (
        same_occurrence
        and first.start_time < second.end_time
        and first.end_time > second.start_time
    )


def timetable_conflict(student, offering, tutorial_group, lab_group):
    selected_meetings = selected_class_meetings(offering, tutorial_group, lab_group)
    if not selected_meetings:
        return None

    registrations = (
        student_models.CourseRegistration.objects.select_related(
            "offering",
            "offering__course",
            "tutorial_group",
            "lab_group",
        )
        .filter(
            student=student,
            offering__semester=offering.semester,
            status__in=ACTIVE_REGISTRATION_STATUSES,
        )
        .exclude(offering=offering)
    )
    for registration in registrations:
        registered_meetings = selected_class_meetings(
            registration.offering,
            registration.tutorial_group,
            registration.lab_group,
        )
        for selected_meeting in selected_meetings:
            for registered_meeting in registered_meetings:
                if meetings_overlap(selected_meeting, registered_meeting):
                    return registered_meeting
    return None


@transaction.atomic
def register_student(
    *,
    student,
    offering,
    actor=None,
    period=None,
    tutorial_group_id=None,
    tutorial_group_code=None,
    lab_group_id=None,
    lab_group_code=None,
    request_note="",
    manual=False,
    allow_credit_override=False,
    allow_capacity_override=False,
):
    if not student or student.role != admin_models.Profile.ROLE_STUDENT:
        return None, "Select a valid student.", status.HTTP_400_BAD_REQUEST
    if not offering or not offering.is_active:
        return None, "Selected course offering is unavailable.", status.HTTP_404_NOT_FOUND

    admin_models.Profile.objects.select_for_update().filter(pk=student.pk).exists()

    semester = offering.semester
    if not manual:
        period = period or active_registration_period(semester)
        if not period:
            return None, "Course registration is not open for this semester.", status.HTTP_403_FORBIDDEN
        if not period.allows_add:
            return None, "This registration phase only allows students to drop courses.", status.HTTP_403_FORBIDDEN
        evaluation_gate = registration_evaluation_gate(student, target_semester=semester)
        if evaluation_gate["blocked"]:
            course_codes = ", ".join(
                survey["course_code"] for survey in evaluation_gate["surveys"]
            )
            label = evaluation_activity_label().lower()
            return (
                None,
                (
                    f"Complete all required {label} activities before registering "
                    f"for the next semester. Pending: {course_codes}."
                ),
                status.HTTP_403_FORBIDDEN,
            )
        if not student_offerings(student, semester).filter(pk=offering.pk).exists():
            return (
                None,
                "This course offering is not available to students from your school, centre, or programme.",
                status.HTTP_403_FORBIDDEN,
            )

    existing = student_models.CourseRegistration.objects.filter(student=student, offering=offering).first()
    active_course_registration = (
        student_models.CourseRegistration.objects.select_related(
            "offering",
            "offering__course",
            "tutorial_group",
            "lab_group",
        )
        .filter(
            student=student,
            offering__course=offering.course,
            status__in=ACTIVE_REGISTRATION_STATUSES,
        )
        .first()
    )
    if active_course_registration:
        return (
            active_course_registration,
            (
                f"Student is already registered for {offering.course.code}. "
                "Drop the current registration before choosing another section or group."
            ),
            status.HTTP_409_CONFLICT,
        )

    passed_record = passed_course_record(student, offering.course, semester)
    if passed_record and not registration_passed_course_retake_allowed():
        return (
            None,
            (
                f"{offering.course.code} was already completed with a passing grade "
                f"({passed_record.grade}). Only failed courses may be retaken."
            ),
            status.HTTP_409_CONFLICT,
        )

    missing = missing_prerequisites(student, offering.course) if registration_prerequisites_required() else []
    if missing:
        courses = ", ".join(f"{course.code} ({course.title})" for course in missing)
        return None, f"Complete the following prerequisite courses before registering: {courses}.", status.HTTP_400_BAD_REQUEST

    tutorial_group, lab_group, error = resolve_group_selection(
        offering,
        tutorial_group_id=tutorial_group_id,
        tutorial_group_code=tutorial_group_code,
        lab_group_id=lab_group_id,
        lab_group_code=lab_group_code,
    )
    if error:
        return None, error, status.HTTP_400_BAD_REQUEST

    conflict = timetable_conflict(student, offering, tutorial_group, lab_group)
    if conflict:
        conflicting_offering = conflict.offering
        label = f"{conflicting_offering.course.code} {conflicting_offering.section}".strip()
        return (
            None,
            (
                f"This course has a timetable conflict with {label}. "
                "Resolve the conflict with the executive before registering."
            ),
            status.HTTP_409_CONFLICT,
        )

    if not allow_capacity_override:
        offering_capacity_error = ensure_offering_capacity(offering, exclude_registration=existing)
        if offering_capacity_error:
            return None, offering_capacity_error, status.HTTP_409_CONFLICT
        capacity_error = ensure_group_capacity(tutorial_group, lab_group, exclude_registration=existing)
        if capacity_error:
            return None, capacity_error, status.HTTP_409_CONFLICT

    total_credits = current_credit_hours(student, semester, exclude_offering=offering) + offering.course.credits
    credit_policy = registration_credit_policy(student=student, semester=semester)
    if not allow_credit_override and total_credits > credit_policy["maximum"]:
        return (
            None,
            f"Registration would exceed the maximum {credit_policy['maximum']} credit hours for this semester.",
            status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        registration = existing or student_models.CourseRegistration(student=student, offering=offering)
        registration.period = period
        registration.tutorial_group = tutorial_group
        registration.lab_group = lab_group
        registration.request_note = request_note
        registration.registered_by = actor or student
        registration.is_manual = manual
        registration.status = student_models.CourseRegistration.STATUS_APPROVED
        registration.approved_by = actor if manual else None
        registration.approved_at = timezone.now()
        registration.decision_note = ""
        registration.save()

        enrollment, _created = student_models.Enrollment.objects.get_or_create(
            student=student,
            offering=offering,
            defaults={"registration": registration, "created_by": actor or student},
        )
        enrollment.registration = registration
        enrollment.tutorial_group = tutorial_group
        enrollment.lab_group = lab_group
        enrollment.created_by = actor or student
        enrollment.completed_at = None
        enrollment.save(update_fields=["registration", "tutorial_group", "lab_group", "created_by", "completed_at"])

    return registration, None, status.HTTP_201_CREATED


def drop_student_course(*, student, offering, actor=None, period=None, manual=False, decision_note=""):
    registration = student_models.CourseRegistration.objects.filter(
        student=student,
        offering=offering,
        status__in=ACTIVE_REGISTRATION_STATUSES,
    ).first()
    if not registration:
        return None, "Active course registration not found.", status.HTTP_404_NOT_FOUND

    if not manual:
        period = period or active_registration_period(offering.semester)
        if not period:
            return None, "Course drop period is not open for this semester.", status.HTTP_403_FORBIDDEN
        if not period.allows_drop:
            return None, "This registration phase does not allow dropping courses.", status.HTTP_403_FORBIDDEN

    registration.status = student_models.CourseRegistration.STATUS_DROPPED
    registration.decision_note = decision_note
    registration.approved_by = actor
    registration.approved_at = timezone.now()
    registration.save(update_fields=["status", "decision_note", "approved_by", "approved_at", "updated_at"])
    student_models.Enrollment.objects.filter(student=student, offering=offering).delete()
    return registration, None, status.HTTP_200_OK


def change_registered_group(
    *,
    registration,
    tutorial_group_id=None,
    tutorial_group_code=None,
    lab_group_id=None,
    lab_group_code=None,
    allow_capacity_override=False,
):
    return (
        "Drop the current course registration and register again to choose a different section or group.",
        status.HTTP_409_CONFLICT,
    )
