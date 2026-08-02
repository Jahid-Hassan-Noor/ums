from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsExecutiveRole
from admin_app.serializers import CourseSerializer, SchoolSerializer, SemesterSerializer, VenueSerializer
from executive_app.course_schedule import (
    class_type_payload,
    create_groups_for_offering,
    courses_for_scope,
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    offerings_for_scope,
    parse_meeting_payload,
    parse_positive_int,
    resolve_meeting_groups,
    scope_payload,
    scope_supports_academic_workflows,
    serialize_offering,
    teachers_payload,
    validate_external_conflicts,
    validate_internal_conflicts,
)
from executive_app.notifications import notify_offering_teachers


def semester_accepts_course_offers(semester, now=None):
    now = now or timezone.now()
    if semester.course_offering_opens_at and semester.course_offering_closes_at:
        return semester.course_offering_opens_at <= now <= semester.course_offering_closes_at
    return semester.is_active


def calendar_group_for_scope(scope):
    if scope.get("kind") == "school":
        return models.Semester.CALENDAR_UNDERGRADUATE
    unit = scope.get("unit")
    if scope.get("kind") != "center" or not unit:
        return None
    code = unit.code.upper()
    if code in {"CFGS", "CGS"}:
        return models.Semester.CALENDAR_FOUNDATION
    if code == "LC":
        return None
    return models.Semester.CALENDAR_UNDERGRADUATE


def semesters_accepting_course_offers(now=None, calendar_group=None):
    now = now or timezone.now()
    semesters = models.Semester.objects.filter(
        Q(is_active=True)
        | Q(
            course_offering_opens_at__lte=now,
            course_offering_closes_at__gte=now,
        )
    )
    if calendar_group:
        semesters = semesters.filter(calendar_group=calendar_group)
    return semesters.distinct()


class ExecutiveCoursesOffer(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
            scope_error = None
        except ValueError as exc:
            scope = {"kind": None, "unit": None}
            scope_error = str(exc)
        if scope.get("kind") and not scope_supports_academic_workflows(scope):
            return Response(
                {
                    "title": "Offer Courses & Scheduling",
                    "section": "executive",
                    "scope": scope_payload(scope),
                    "scope_error": non_academic_scope_response(scope)["detail"],
                    "courses": [],
                    "schools": [],
                    "semesters": [],
                    "teachers": [],
                    "venues": [],
                    "class_types": [],
                    "offerings": [],
                },
                status=status.HTTP_200_OK,
            )

        courses = courses_for_scope(scope).filter(is_active=True)
        schools = models.School.objects.filter(is_active=True)
        if scope.get("kind") == "school":
            schools = schools.exclude(pk=scope["unit"].pk)
        calendar_group = calendar_group_for_scope(scope)
        semesters = (
            semesters_accepting_course_offers(calendar_group=calendar_group).order_by("-start_date")
            if calendar_group
            else models.Semester.objects.none()
        )
        venues = models.Venue.objects.filter(is_active=True).order_by("building__name", "name")

        return Response(
            {
                "title": "Offer Courses & Scheduling",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
                "courses": CourseSerializer(courses, many=True).data,
                "schools": SchoolSerializer(schools.order_by("name"), many=True).data,
                "semesters": SemesterSerializer(semesters, many=True).data,
                "teachers": teachers_payload(scope),
                "venues": VenueSerializer(venues, many=True).data,
                "class_types": class_type_payload(),
                "offerings": [
                    serialize_offering(offering)
                    for offering in offerings_for_scope(scope)
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope.get("kind"):
            return Response(
                {"detail": "Executive must be assigned to one school or centre before offering courses."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        data = request.data
        course_id = data.get("course_id")
        semester_id = data.get("semester_id")
        instructor_id = data.get("instructor_id")
        section = str(data.get("section", "")).strip()
        capacity = parse_positive_int(data.get("capacity"), default=40)
        eligible_school_ids = data.get("eligible_school_ids", [])
        meetings = data.get("meetings", [])
        tutorial_groups = data.get("tutorial_groups", [])

        if not course_id or not semester_id:
            return Response(
                {"detail": "Course and semester are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not capacity:
            return Response(
                {"detail": "Capacity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(eligible_school_ids, list):
            return Response(
                {"detail": "Eligible schools must be provided as a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            eligible_school_ids = {int(value) for value in eligible_school_ids}
        except (TypeError, ValueError):
            return Response(
                {"detail": "Eligible schools contain an invalid selection."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        eligible_schools = models.School.objects.filter(
            pk__in=eligible_school_ids,
            is_active=True,
        )
        if eligible_schools.count() != len(eligible_school_ids):
            return Response(
                {"detail": "Eligible schools contain an invalid selection."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if scope.get("kind") == "school":
            eligible_schools = eligible_schools.exclude(pk=scope["unit"].pk)
        if not isinstance(meetings, list) or not meetings:
            return Response(
                {"detail": "Add at least one lecture or lab class before offering the course."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = courses_for_scope(scope).filter(pk=course_id, is_active=True).first()
        if not course:
            return Response(
                {"detail": "Invalid course selection for this executive scope."},
                status=status.HTTP_404_NOT_FOUND,
            )

        semester = models.Semester.objects.filter(pk=semester_id).first()
        if not semester:
            return Response(
                {"detail": "Invalid semester selection."},
                status=status.HTTP_404_NOT_FOUND,
            )
        calendar_group = calendar_group_for_scope(scope)
        if not calendar_group or semester.calendar_group != calendar_group:
            return Response(
                {"detail": "This semester does not belong to the executive's academic calendar."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not semester_accepts_course_offers(semester):
            return Response(
                {"detail": "The course-offering window is closed for this semester."},
                status=status.HTTP_403_FORBIDDEN,
            )

        instructor = None
        if instructor_id:
            instructor = models.Profile.objects.filter(
                pk=instructor_id,
                role=models.Profile.ROLE_TEACHER,
                is_active=True,
            ).select_related("user").first()
            if not instructor:
                return Response(
                    {"detail": "Selected instructor is unavailable."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        parsed_meetings = []
        for index, meeting in enumerate(meetings, start=1):
            parsed, error = parse_meeting_payload(meeting, index, default_lecturer_id=instructor_id)
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
            parsed_meetings.append(parsed)

        internal_conflict = validate_internal_conflicts(parsed_meetings)
        if internal_conflict:
            return Response({"detail": internal_conflict}, status=status.HTTP_400_BAD_REQUEST)

        lecture_count = sum(
            1
            for meeting in parsed_meetings
            if meeting["class_type"] == models.ClassMeeting.CLASS_TYPE_LECTURE
        )
        lab_count = sum(
            1
            for meeting in parsed_meetings
            if meeting["class_type"] == models.ClassMeeting.CLASS_TYPE_LAB
        )
        if lecture_count < semester.default_classes_per_week:
            return Response(
                {
                    "detail": (
                        f"{semester.name} requires at least {semester.default_classes_per_week} "
                        "lecture/tutorial class meeting(s) per course."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if course.has_lab and lab_count < 1:
            return Response(
                {"detail": "This course is marked as having lab classes. Add at least one lab class."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not course.has_lab and lab_count:
            return Response(
                {"detail": "Only courses marked as having lab classes can include lab meetings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        external_conflict = validate_external_conflicts(semester, parsed_meetings)
        if external_conflict:
            return Response({"detail": external_conflict}, status=status.HTTP_409_CONFLICT)

        if not instructor and parsed_meetings:
            instructor = parsed_meetings[0]["lecturer"]

        try:
            with transaction.atomic():
                offering = models.CourseOffering.objects.create(
                    course=course,
                    semester=semester,
                    instructor=instructor,
                    section=section,
                    capacity=capacity,
                    is_active=True,
                )
                offering.eligible_schools.set(eligible_schools)
                created_groups = create_groups_for_offering(offering, tutorial_groups)
                default_tutorial_group = created_groups[0] if created_groups else None

                for meeting_data in parsed_meetings:
                    tutorial_group, lab_group, group_error = resolve_meeting_groups(
                        offering,
                        meeting_data,
                        default_tutorial_group=default_tutorial_group,
                    )
                    if group_error:
                        raise ValueError(group_error)
                    models.ClassMeeting.objects.create(
                        offering=offering,
                        semester=semester,
                        tutorial_group=tutorial_group,
                        lab_group=lab_group,
                        day_of_week=meeting_data["day_of_week"],
                        start_time=meeting_data["start_time"],
                        end_time=meeting_data["end_time"],
                        lecturer=meeting_data["lecturer"],
                        venue=meeting_data["venue"],
                        class_type=meeting_data["class_type"],
                        status=models.ClassMeeting.STATUS_SCHEDULED,
                    )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"detail": "This course is already offered for the selected semester and section."},
                status=status.HTTP_409_CONFLICT,
            )

        offering = offerings_for_scope(scope).get(pk=offering.pk)
        notify_offering_teachers(
            offering,
            profile,
            event_type="courses.assigned",
            verb=f"You were assigned to {offering.course.code} for {offering.semester.name}.",
        )
        return Response(
            {
                "message": "Course offered and scheduled successfully.",
                "offering": serialize_offering(offering),
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        offering_id = request.query_params.get("offering_id")
        if not offering_id:
            return Response(
                {"detail": "offering_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        offering = offerings_for_scope(scope).filter(pk=offering_id).first()
        if not offering:
            return Response(
                {"detail": "Course offering not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        offering.delete()
        return Response(
            {"message": "Course offering and scheduled classes deleted successfully."},
            status=status.HTTP_200_OK,
        )
