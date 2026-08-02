from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile, teacher_offerings
from teacher_app.course_content_service import serialize_assessment_plan


def serialize_teacher_course(offering):
    assessment = serialize_assessment_plan(offering)
    return {
        "id": offering.id,
        "code": offering.course.code,
        "title": offering.course.title,
        "section": offering.section,
        "semester": offering.semester.name,
        "semester_active": offering.semester.is_active,
        "has_lab": offering.course.has_lab,
        "is_active": offering.is_active,
        "assessment": assessment,
        "has_study_guide": bool(assessment["study_guide"]),
        "assignment_count": offering.assignment_set.count(),
        "section_count": offering.course_sections.count(),
        "resource_count": offering.course_resources.count(),
        "student_count": offering.enrollment_set.filter(completed_at__isnull=True).count(),
    }


class TeacherCourses(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        offerings = teacher_offerings(profile, include_inactive=True)
        return Response(
            {
                "title": "Courses",
                "section": "teacher",
                "courses": [serialize_teacher_course(offering) for offering in offerings],
            },
            status=status.HTTP_200_OK,
        )
