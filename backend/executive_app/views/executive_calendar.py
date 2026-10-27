from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from admin_app.models import AcademicEvent
from admin_app.schedule import serialize_schedule_event
from auth_app.permissions import IsExecutiveRole
from executive_app.course_schedule import (
    course_scope_filter,
    get_executive_profile,
    get_executive_scope,
    scope_payload,
)


class ExecutiveCalendar(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        try:
            scope = get_executive_scope(get_executive_profile(request.user))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope.get("kind"):
            return Response(
                {"detail": "Executive must be assigned to one school or centre."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kind = scope["kind"]
        unit = scope["unit"]
        linked_scope = (
            Q(**{f"program__{kind}": unit})
            | (
                Q(program__isnull=True)
                & (
                    course_scope_filter(scope, "offering__course__")
                    | course_scope_filter(scope, "class_meeting__offering__course__")
                )
            )
        )
        events = (
            AcademicEvent.objects.select_related("offering__course", "class_meeting__offering__course")
            .filter(
                Q(**{kind: unit})
                | (Q(school__isnull=True, center__isnull=True) & linked_scope)
            )
            .distinct()
            .order_by("starts_at", "title")
        )
        serialized = []
        for event in events:
            payload = serialize_schedule_event(event)
            offering = event.offering or (event.class_meeting.offering if event.class_meeting_id else None)
            if offering:
                payload.update({
                    "course_code": offering.course.code,
                    "course_title": offering.course.title,
                    "offering_id": offering.id,
                    "href": "/executive/manage/schedule",
                })
            serialized.append(payload)

        return Response({
            "title": "Calendar",
            "section": "executive",
            "scope": scope_payload(scope),
            "schedule": {"events": serialized, "count": len(serialized), "semester": None},
        })

