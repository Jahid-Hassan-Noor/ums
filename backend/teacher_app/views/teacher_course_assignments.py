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


class TeacherCourseAssignments(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request, course_id):
        profile = get_teacher_profile(request.user)
        offering = teacher_offerings(profile).filter(pk=course_id).first()
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        assignments = (
            Assignment.objects.select_related("offering", "offering__course", "offering__semester", "created_by", "created_by__user")
            .filter(offering=offering)
            .order_by("-created_at")
        )
        return Response(
            {
                "title": "Course Assignments",
                "section": "teacher",
                "course": {
                    "id": offering.id,
                    "code": offering.course.code,
                    "title": offering.course.title,
                    "section": offering.section,
                },
                "assignments": [serialize_assignment(assignment) for assignment in assignments],
            },
            status=status.HTTP_200_OK,
        )
