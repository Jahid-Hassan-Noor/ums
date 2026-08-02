from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import (
    get_teacher_profile,
    serialize_assignment,
    teacher_offerings,
)
from teacher_app.models import Assignment


class TeacherAssignments(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        assignments = (
            Assignment.objects.select_related(
                "offering",
                "offering__course",
                "offering__semester",
                "created_by",
                "created_by__user",
            )
            .filter(offering__in=teacher_offerings(profile))
            .annotate(
                submission_count=Count("assignmentsubmission", distinct=True),
                graded_count=Count(
                    "assignmentsubmission",
                    filter=Q(assignmentsubmission__status="graded"),
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )
        return Response(
            {
                "title": "Assignments",
                "section": "teacher",
                "assignments": [serialize_assignment(assignment) for assignment in assignments],
            },
            status=status.HTTP_200_OK,
        )
