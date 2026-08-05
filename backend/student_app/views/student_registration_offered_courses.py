from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.registration_service import (
    active_registration_period,
    active_semester,
    get_student_profile,
    registration_credit_policy,
    serialize_offering_for_registration,
    student_offerings,
)
from student_app.serializers import RegistrationPeriodSerializer


class StudentRegistrationOfferedCourses(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        semester = active_semester(
            request.query_params.get("semester_id"),
            student=student,
            prefer_registration=True,
        )
        period = active_registration_period(semester)
        offerings = student_offerings(student, semester) if student and semester else []
        credit_policy = registration_credit_policy(student=student, semester=semester) if semester else None
        return Response(
            {
                "title": "Offered Courses",
                "section": "student",
                "semester": {
                    "id": semester.id,
                    "name": semester.name,
                    "max_credit_hours": credit_policy["maximum"],
                }
                if semester
                else None,
                "credit_hours": credit_policy
                if credit_policy
                else {"minimum": 0, "maximum": 0, "source": ""},
                "current_phase": RegistrationPeriodSerializer(period).data if period else None,
                "offerings": [
                    serialize_offering_for_registration(offering, student=student)
                    for offering in offerings
                ],
            },
            status=status.HTTP_200_OK,
        )
