from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from core.common.profiles import profile_display_name, profile_identifier
from student_app.models import Enrollment
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import attendance_summary_for_offering
from teacher_app.course_content_service import offering_for_teacher


class TeacherCourseRoster(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request, course_id):
        teacher = get_teacher_profile(request.user)
        offering = offering_for_teacher(teacher, course_id)
        if not offering:
            return Response(
                {"detail": "Course offering not found for this teacher."},
                status=status.HTTP_404_NOT_FOUND,
            )

        attendance_by_student = {
            row["student_id"]: row
            for row in attendance_summary_for_offering(offering)
        }
        enrollments = (
            Enrollment.objects.select_related(
                "student",
                "student__user",
                "student__student_detail",
                "tutorial_group",
                "lab_group",
            )
            .filter(offering=offering, completed_at__isnull=True)
            .order_by(
                "student__student_detail__student_id",
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        students = []
        for enrollment in enrollments:
            attendance = attendance_by_student.get(enrollment.student_id, {})
            students.append(
                {
                    "profile_id": enrollment.student_id,
                    "name": profile_display_name(enrollment.student),
                    "username": enrollment.student.user.username,
                    "email": enrollment.student.user.email,
                    "student_number": profile_identifier(enrollment.student),
                    "tutorial_group": (
                        enrollment.tutorial_group.code
                        if enrollment.tutorial_group_id
                        else ""
                    ),
                    "lab_group": (
                        enrollment.lab_group.code if enrollment.lab_group_id else ""
                    ),
                    "enrolled_at": enrollment.enrolled_at.isoformat(),
                    "attended": attendance.get("attended", 0),
                    "total_classes": attendance.get("total_classes", 0),
                    "attendance_percentage": attendance.get(
                        "attendance_percentage", 0
                    ),
                }
            )

        return Response(
            {
                "title": "Course Roster",
                "section": "teacher",
                "course": {
                    "id": offering.id,
                    "code": offering.course.code,
                    "title": offering.course.title,
                    "section": offering.section,
                    "semester": offering.semester.name,
                },
                "summary": {
                    "students": len(students),
                    "tutorial_groups": len(
                        {row["tutorial_group"] for row in students if row["tutorial_group"]}
                    ),
                    "lab_groups": len(
                        {row["lab_group"] for row in students if row["lab_group"]}
                    ),
                    "attendance_sessions": max(
                        (row["total_classes"] for row in students),
                        default=0,
                    ),
                },
                "students": students,
            },
            status=status.HTTP_200_OK,
        )
