from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsExecutiveRole
from admin_app.serializers import VenueSerializer
from executive_app.course_schedule import (
    build_schedule_xlsx,
    class_type_payload,
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    offerings_for_scope,
    parse_meeting_payload,
    schedule_rows_for_scope,
    scope_payload,
    scope_supports_academic_workflows,
    serialize_meeting,
    teachers_payload,
    validate_external_conflicts,
)
from executive_app.final_exam_schedule import (
    FinalExamScheduleError,
    delete_final_exam,
    final_exam_options,
    final_exams_for_offerings,
    save_final_exam,
    serialize_final_exam,
)
from executive_app.notifications import notify_meeting_change


def _final_exam_error_response(exc):
    payload = {"detail": exc.detail}
    if exc.conflicts:
        payload["conflicts"] = exc.conflicts
    return Response(payload, status=exc.status_code)


class ExecutiveManageSchedule(APIView):
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
                    "title": "Schedule",
                    "section": "executive",
                    "scope": scope_payload(scope),
                    "scope_error": non_academic_scope_response(scope)["detail"],
                    "teachers": [],
                    "venues": [],
                    "class_types": [],
                    "meetings": [],
                    "exam_offerings": [],
                    "final_exams": [],
                },
                status=status.HTTP_200_OK,
            )

        meetings = schedule_rows_for_scope(scope)
        offerings = offerings_for_scope(scope)
        if request.query_params.get("export") == "xlsx":
            content = build_schedule_xlsx(meetings)
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="executive-schedule.xlsx"'
            return response

        venues = models.Venue.objects.filter(is_active=True).order_by("building__name", "name")
        return Response(
            {
                "title": "Schedule",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
                "teachers": teachers_payload(scope),
                "venues": VenueSerializer(venues, many=True).data,
                "class_types": class_type_payload(),
                "meetings": [serialize_meeting(meeting) for meeting in meetings],
                "exam_offerings": final_exam_options(offerings),
                "final_exams": [
                    serialize_final_exam(exam)
                    for exam in final_exams_for_offerings(offerings)
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
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        if request.data.get("schedule_kind") == "final_exam":
            try:
                exam = save_final_exam(
                    offerings=offerings_for_scope(scope),
                    payload=request.data,
                )
            except FinalExamScheduleError as exc:
                return _final_exam_error_response(exc)
            return Response(
                {
                    "message": "Final exam schedule saved successfully.",
                    "final_exam": serialize_final_exam(exam),
                },
                status=status.HTTP_200_OK if request.data.get("exam_id") else status.HTTP_201_CREATED,
            )

        recurring_id = request.data.get("recurring_meeting_id") or request.data.get("meeting_id")
        recurring_meeting = (
            models.ClassMeeting.objects.select_related("offering", "offering__semester")
            .filter(
                pk=recurring_id,
                offering__in=schedule_rows_for_scope(scope).values("offering_id"),
                recurring_meeting__isnull=True,
            )
            .first()
        )
        if not recurring_meeting:
            return Response(
                {"detail": "Semester class meeting not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {
            "meeting_date": request.data.get("meeting_date"),
            "start_time": request.data.get("start_time", recurring_meeting.start_time.isoformat(timespec="minutes")),
            "end_time": request.data.get("end_time", recurring_meeting.end_time.isoformat(timespec="minutes")),
            "venue_id": request.data.get("venue_id", recurring_meeting.venue_id),
            "lecturer_id": request.data.get("lecturer_id", recurring_meeting.lecturer_id),
            "class_type": request.data.get("class_type", recurring_meeting.class_type),
        }
        parsed, error = parse_meeting_payload(payload, 1, require_date=True)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        adjustment = models.ClassMeeting.objects.filter(
            recurring_meeting=recurring_meeting,
            meeting_date=parsed["meeting_date"],
        ).first()
        exclude_ids = {recurring_meeting.id}
        if adjustment:
            exclude_ids.add(adjustment.id)

        conflict = validate_external_conflicts(
            recurring_meeting.offering.semester,
            [parsed],
            exclude_meeting_ids=exclude_ids,
        )
        if conflict:
            return Response({"detail": conflict}, status=status.HTTP_409_CONFLICT)

        if not adjustment:
            adjustment = models.ClassMeeting(
                offering=recurring_meeting.offering,
                semester=recurring_meeting.semester,
                recurring_meeting=recurring_meeting,
            )

        adjustment.meeting_date = parsed["meeting_date"]
        adjustment.day_of_week = parsed["day_of_week"]
        adjustment.start_time = parsed["start_time"]
        adjustment.end_time = parsed["end_time"]
        adjustment.venue = parsed["venue"]
        adjustment.lecturer = parsed["lecturer"]
        adjustment.class_type = parsed["class_type"]
        adjustment.tutorial_group = recurring_meeting.tutorial_group
        adjustment.lab_group = recurring_meeting.lab_group
        adjustment.status = models.ClassMeeting.STATUS_SCHEDULED
        adjustment.save()
        notify_meeting_change(
            adjustment,
            profile,
            event_type="schedule.changed",
            verb=f"Single-week schedule updated for {adjustment.offering.course.code}.",
        )

        return Response(
            {
                "message": "Single-week class schedule updated successfully.",
                "meeting": serialize_meeting(adjustment),
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

        exam_id = request.query_params.get("exam_id")
        if exam_id:
            try:
                delete_final_exam(
                    offerings=offerings_for_scope(scope),
                    exam_id=exam_id,
                )
            except FinalExamScheduleError as exc:
                return _final_exam_error_response(exc)
            return Response({"message": "Final exam schedule removed."}, status=status.HTTP_200_OK)

        adjustment_id = request.query_params.get("adjustment_id")
        adjustment = (
            models.ClassMeeting.objects.filter(
                pk=adjustment_id,
                offering__in=schedule_rows_for_scope(scope).values("offering_id"),
                recurring_meeting__isnull=False,
            )
            .first()
        )
        if not adjustment:
            return Response(
                {"detail": "Single-week schedule adjustment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        adjustment.delete()
        return Response({"message": "Single-week adjustment removed."}, status=status.HTTP_200_OK)
