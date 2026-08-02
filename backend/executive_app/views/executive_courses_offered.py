from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsExecutiveRole
from admin_app.serializers import SemesterSerializer, VenueSerializer
from executive_app.course_schedule import (
    class_type_payload,
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    offerings_for_scope,
    parse_meeting_payload,
    parse_positive_int,
    resolve_meeting_groups,
    scope_payload,
    scope_supports_academic_workflows,
    serialize_meeting,
    serialize_offering,
    teachers_payload,
    validate_external_conflicts,
)
from executive_app.notifications import notify_meeting_change, notify_offering_teachers


class ExecutiveCoursesOffered(APIView):
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
                    "title": "Offered Courses",
                    "section": "executive",
                    "scope": scope_payload(scope),
                    "scope_error": non_academic_scope_response(scope)["detail"],
                    "semesters": [],
                    "teachers": [],
                    "venues": [],
                    "class_types": [],
                    "offerings": [],
                },
                status=status.HTTP_200_OK,
            )

        venues = models.Venue.objects.filter(is_active=True).order_by("building__name", "name")
        semesters = models.Semester.objects.filter(is_active=True).order_by("-start_date")

        return Response(
            {
                "title": "Offered Courses",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
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

    def patch(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        meeting_id = request.query_params.get("meeting_id")
        offering_id = request.query_params.get("offering_id")
        if meeting_id:
            return self._patch_meeting(scope, meeting_id, request.data, profile)
        if offering_id:
            return self._patch_offering(scope, offering_id, request.data, profile)
        return Response(
            {"detail": "meeting_id or offering_id parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _patch_offering(self, scope, offering_id, data, profile):
        offering = offerings_for_scope(scope).filter(pk=offering_id).first()
        if not offering:
            return Response({"detail": "Course offering not found."}, status=status.HTTP_404_NOT_FOUND)

        capacity = parse_positive_int(data.get("capacity"), default=offering.capacity)
        if not capacity:
            return Response(
                {"detail": "Capacity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instructor = offering.instructor
        instructor_id = data.get("instructor_id")
        if instructor_id not in (None, ""):
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

        offering.section = str(data.get("section", offering.section)).strip()
        offering.capacity = capacity
        offering.instructor = instructor
        if "is_active" in data:
            offering.is_active = bool(data.get("is_active"))
        offering.save(update_fields=["section", "capacity", "instructor", "is_active", "updated_at"])
        notify_offering_teachers(
            offering,
            profile,
            event_type="courses.assignment_changed",
            verb=f"Course assignment updated: {offering.course.code}.",
        )
        return Response(
            {
                "message": "Course offering updated successfully.",
                "offering": serialize_offering(offerings_for_scope(scope).get(pk=offering.pk)),
            },
            status=status.HTTP_200_OK,
        )

    def _patch_meeting(self, scope, meeting_id, data, profile):
        meeting = (
            models.ClassMeeting.objects.select_related("offering", "offering__semester")
            .filter(pk=meeting_id, offering__in=offerings_for_scope(scope), recurring_meeting__isnull=True)
            .first()
        )
        if not meeting:
            return Response({"detail": "Semester class meeting not found."}, status=status.HTTP_404_NOT_FOUND)

        payload = {
            "day_of_week": data.get("day_of_week", meeting.day_of_week),
            "start_time": data.get("start_time", meeting.start_time.isoformat(timespec="minutes")),
            "end_time": data.get("end_time", meeting.end_time.isoformat(timespec="minutes")),
            "venue_id": data.get("venue_id", meeting.venue_id),
            "lecturer_id": data.get("lecturer_id", meeting.lecturer_id),
            "class_type": data.get("class_type", meeting.class_type),
            "tutorial_group_code": data.get(
                "tutorial_group_code",
                meeting.tutorial_group.code if meeting.tutorial_group_id else "",
            ),
            "lab_group_code": data.get(
                "lab_group_code",
                meeting.lab_group.code if meeting.lab_group_id else "",
            ),
        }
        parsed, error = parse_meeting_payload(payload, 1)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        tutorial_group, lab_group, group_error = resolve_meeting_groups(
            meeting.offering,
            parsed,
            default_tutorial_group=meeting.tutorial_group,
        )
        if group_error:
            return Response({"detail": group_error}, status=status.HTTP_400_BAD_REQUEST)

        conflict = validate_external_conflicts(
            meeting.offering.semester,
            [parsed],
            exclude_meeting_ids={meeting.id},
        )
        if conflict:
            return Response({"detail": conflict}, status=status.HTTP_409_CONFLICT)

        meeting.day_of_week = parsed["day_of_week"]
        meeting.start_time = parsed["start_time"]
        meeting.end_time = parsed["end_time"]
        meeting.venue = parsed["venue"]
        meeting.lecturer = parsed["lecturer"]
        meeting.class_type = parsed["class_type"]
        meeting.tutorial_group = tutorial_group
        meeting.lab_group = lab_group
        meeting.status = models.ClassMeeting.STATUS_SCHEDULED
        meeting.save(
            update_fields=[
                "day_of_week",
                "start_time",
                "end_time",
                "venue",
                "lecturer",
                "class_type",
                "tutorial_group",
                "lab_group",
                "status",
                "updated_at",
            ]
        )
        notify_meeting_change(
            meeting,
            profile,
            event_type="schedule.changed",
            verb=f"Schedule updated for {meeting.offering.course.code}.",
        )

        return Response(
            {
                "message": "Semester class schedule updated successfully.",
                "meeting": serialize_meeting(meeting),
            },
            status=status.HTTP_200_OK,
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
            return Response({"detail": "Course offering not found."}, status=status.HTTP_404_NOT_FOUND)
        offering.delete()
        return Response({"message": "Course offering removed successfully."}, status=status.HTTP_200_OK)
