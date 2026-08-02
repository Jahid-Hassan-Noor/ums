from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.models import CourseRegistration
from student_app.registration_service import active_semester, get_student_profile
from student_app.serializers import CourseRegistrationSerializer


class StudentRegistrationRequests(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        semester = active_semester(
            request.query_params.get("semester_id"),
            student=student,
            prefer_registration=True,
        )
        registrations = CourseRegistration.objects.none()
        if student:
            registrations = CourseRegistration.objects.select_related(
                "offering",
                "offering__course",
                "offering__semester",
                "period",
                "tutorial_group",
                "lab_group",
            ).filter(student=student)
            if semester:
                registrations = registrations.filter(offering__semester=semester)

        return Response(
            {
                "title": "My Registrations",
                "section": "student",
                "semester": {
                    "id": semester.id,
                    "name": semester.name,
                }
                if semester
                else None,
                "registrations": CourseRegistrationSerializer(
                    registrations.order_by("-created_at"),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )
