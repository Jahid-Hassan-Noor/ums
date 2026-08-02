from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models as admin_models
from auth_app.permissions import IsStudentRole
from executive_app.evaluation_service import registration_evaluation_gate
from student_app.models import CourseRegistration
from student_app.registration_service import (
    active_registration_period,
    active_semester,
    current_credit_hours,
    drop_student_course,
    get_student_profile,
    register_student,
    serialize_offering_for_registration,
    student_offerings,
)
from student_app.serializers import CourseRegistrationSerializer, RegistrationPeriodSerializer


def registration_payload(student, semester):
    period = active_registration_period(semester)
    evaluation_gate = registration_evaluation_gate(student, target_semester=semester)
    registrations = (
        CourseRegistration.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "period",
            "tutorial_group",
            "lab_group",
        )
        .filter(student=student, offering__semester=semester)
        .order_by("-created_at")
    )
    offerings = student_offerings(student, semester)
    return {
        "title": "Course Registration",
        "section": "student",
        "semester": {
            "id": semester.id,
            "name": semester.name,
            "semester_type": semester.semester_type,
            "academic_session": semester.academic_session,
            "max_credit_hours": semester.max_credit_hours,
        }
        if semester
        else None,
        "current_phase": RegistrationPeriodSerializer(period).data if period else None,
        "can_add": bool(period and period.allows_add and not evaluation_gate["blocked"]),
        "can_drop": bool(period and period.allows_drop),
        "evaluation_gate": evaluation_gate,
        "credit_hours": {
            "registered": current_credit_hours(student, semester) if semester else 0,
            "maximum": semester.max_credit_hours if semester else 0,
        },
        "offerings": [serialize_offering_for_registration(offering) for offering in offerings],
        "registrations": CourseRegistrationSerializer(registrations, many=True).data,
    }


class StudentCoursesRegister(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        semester = active_semester(
            request.query_params.get("semester_id"),
            student=student,
            prefer_registration=True,
        )
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        if not semester:
            return Response(
                {
                    "title": "Course Registration",
                    "section": "student",
                    "semester": None,
                    "current_phase": None,
                    "can_add": False,
                    "can_drop": False,
                    "evaluation_gate": {
                        "blocked": False,
                        "pending_count": 0,
                        "message": "",
                        "surveys": [],
                    },
                    "credit_hours": {
                        "registered": 0,
                        "maximum": 0,
                    },
                    "offerings": [],
                    "registrations": [],
                },
                status=status.HTTP_200_OK,
            )
        return Response(registration_payload(student, semester), status=status.HTTP_200_OK)

    def post(self, request):
        student = get_student_profile(request.user)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "register")).strip().lower()
        offering = admin_models.CourseOffering.objects.select_related("course", "semester").filter(
            pk=request.data.get("offering_id"),
            is_active=True,
        ).first()
        if not offering:
            return Response({"detail": "Course offering not found."}, status=status.HTTP_404_NOT_FOUND)

        if action == "drop":
            registration, error, response_status = drop_student_course(
                student=student,
                offering=offering,
                actor=student,
                decision_note=str(request.data.get("decision_note", "")).strip(),
            )
        else:
            registration, error, response_status = register_student(
                student=student,
                offering=offering,
                actor=student,
                tutorial_group_id=request.data.get("tutorial_group_id"),
                tutorial_group_code=request.data.get("tutorial_group_code"),
                lab_group_id=request.data.get("lab_group_id"),
                lab_group_code=request.data.get("lab_group_code"),
                request_note=str(request.data.get("request_note", "")).strip(),
            )

        if error:
            return Response({"detail": error}, status=response_status)

        return Response(
            {
                "message": "Course dropped successfully." if action == "drop" else "Course registered successfully.",
                "registration": CourseRegistrationSerializer(registration).data,
            },
            status=response_status,
        )
