from rest_framework import status
from auth_app.permissions import IsStudentRole
from rest_framework.response import Response
from rest_framework.views import APIView
from student_app.models import Enrollment
from student_app.registration_service import active_semester, get_student_profile, profile_display_name
from teacher_app.attendance_service import student_attendance_summary


class StudentCoursesCurrent(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        semester = active_semester(request.query_params.get("semester_id"), student=student)
        enrollments = Enrollment.objects.none()
        if student:
            enrollments = (
                Enrollment.objects.select_related(
                    "offering",
                    "offering__course",
                    "offering__semester",
                    "offering__instructor",
                    "offering__instructor__user",
                    "tutorial_group",
                    "lab_group",
                )
                .filter(student=student, completed_at__isnull=True)
                .order_by("offering__course__code", "offering__section")
            )
            if semester:
                enrollments = enrollments.filter(offering__semester=semester)

        attendance_by_offering = {
            item["offering_id"]: item
            for item in (student_attendance_summary(student, semester=semester) if student else [])
        }
        courses = []
        total_credits = 0
        for enrollment in enrollments:
            offering = enrollment.offering
            total_credits += offering.course.credits
            attendance = attendance_by_offering.get(offering.id)
            courses.append(
                {
                    "id": enrollment.id,
                    "offering_id": offering.id,
                    "course": {
                        "id": offering.course_id,
                        "code": offering.course.code,
                        "title": offering.course.title,
                        "credits": offering.course.credits,
                        "has_lab": offering.course.has_lab,
                    },
                    "semester": {
                        "id": offering.semester_id,
                        "name": offering.semester.name,
                        "academic_session": offering.semester.academic_session,
                    },
                    "section": offering.section,
                    "instructor": profile_display_name(offering.instructor),
                    "tutorial_group": enrollment.tutorial_group.code if enrollment.tutorial_group_id else "",
                    "lab_group": enrollment.lab_group.code if enrollment.lab_group_id else "",
                    "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
                    "attendance_percentage": attendance["attendance_percentage"] if attendance else 0,
                    "attendance_summary": attendance
                    or {
                        "attended": 0,
                        "total_classes": 0,
                        "attendance_percentage": 0,
                    },
                }
            )

        return Response(
            {
                "title": "Current Courses",
                "section": "student",
                "semester": {
                    "id": semester.id,
                    "name": semester.name,
                    "academic_session": semester.academic_session,
                    "max_credit_hours": semester.max_credit_hours,
                }
                if semester
                else None,
                "summary": {
                    "course_count": len(courses),
                    "registered_credit_hours": total_credits,
                    "max_credit_hours": semester.max_credit_hours if semester else 0,
                },
                "courses": courses,
            },
            status=status.HTTP_200_OK,
        )
