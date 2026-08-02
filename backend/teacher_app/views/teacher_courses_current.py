from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile, teacher_offerings
from teacher_app.views.teacher_courses import serialize_teacher_course


class TeacherCoursesCurrent(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        offerings = teacher_offerings(profile).filter(semester__is_active=True)
        return Response(
            {
                "title": "Current Courses",
                "section": "teacher",
                "courses": [serialize_teacher_course(offering) for offering in offerings],
            },
            status=status.HTTP_200_OK,
        )
