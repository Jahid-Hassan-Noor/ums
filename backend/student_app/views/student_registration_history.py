from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.models import CourseRegistration
from student_app.registration_service import get_student_profile
from student_app.serializers import CourseRegistrationSerializer


class StudentRegistrationHistory(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        registrations = []
        if student:
            registrations = list(
                CourseRegistration.objects.select_related(
                    "offering",
                    "offering__course",
                    "offering__semester",
                    "period",
                    "tutorial_group",
                    "lab_group",
                )
                .filter(student=student)
                .order_by("-offering__semester__start_date", "-created_at")
            )

        status_counts = {
            CourseRegistration.STATUS_PENDING: 0,
            CourseRegistration.STATUS_APPROVED: 0,
            CourseRegistration.STATUS_REJECTED: 0,
            CourseRegistration.STATUS_DROPPED: 0,
        }
        semester_ids = set()
        credit_hours = 0
        for registration in registrations:
            status_counts[registration.status] = status_counts.get(registration.status, 0) + 1
            semester_ids.add(registration.offering.semester_id)
            if registration.status == CourseRegistration.STATUS_APPROVED:
                credit_hours += registration.offering.course.credits

        return Response(
            {
                "title": "Registration History",
                "section": "student",
                "summary": {
                    "total": len(registrations),
                    "pending": status_counts[CourseRegistration.STATUS_PENDING],
                    "approved": status_counts[CourseRegistration.STATUS_APPROVED],
                    "rejected": status_counts[CourseRegistration.STATUS_REJECTED],
                    "dropped": status_counts[CourseRegistration.STATUS_DROPPED],
                    "credit_hours": credit_hours,
                    "semesters": len(semester_ids),
                },
                "registrations": CourseRegistrationSerializer(registrations, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
