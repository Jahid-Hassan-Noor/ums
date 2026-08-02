from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models as admin_models
from auth_app.permissions import IsExecutiveRole
from core.common.request_utils import parse_bool as _parse_bool
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    non_academic_scope_response,
    offerings_for_scope,
    scope_payload,
    scope_supports_academic_workflows,
    serialize_offering,
)
from student_app.models import CourseRegistration
from student_app.registration_service import (
    change_registered_group,
    drop_student_course,
    register_student,
)
from student_app.serializers import CourseRegistrationSerializer


def students_for_scope(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return admin_models.Profile.objects.none()
    profile_scope = Q(**{f"student_detail__{kind}": unit}) | Q(
        **{f"student_detail__program__{kind}": unit}
    )
    return (
        admin_models.Profile.objects.select_related(
            "user",
            "student_detail",
            "student_detail__school",
            "student_detail__center",
            "student_detail__program",
        )
        .filter(role=admin_models.Profile.ROLE_STUDENT, is_active=True)
        .filter(profile_scope)
        .order_by("user__first_name", "user__last_name", "student_detail__student_id")
    )


def serialize_student(profile):
    user = profile.user
    return {
        "id": profile.id,
        "name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "username": user.username,
        "email": user.email,
        "student_id": profile.student_id,
        "school": profile.school.code if profile.school_id else "",
        "center": profile.center.code if profile.center_id else "",
        "program": profile.program.code if profile.program_id else "",
        "phone": profile.phone,
    }


class ExecutiveManageStudents(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
            scope_error = None
        except ValueError as exc:
            scope = {"kind": None, "unit": None}
            scope_error = str(exc)
        if scope.get("kind") and not scope_supports_academic_workflows(scope):
            return Response(
                {
                    "title": "Manage Students",
                    "section": "executive",
                    "scope": scope_payload(scope),
                    "scope_error": non_academic_scope_response(scope)["detail"],
                    "students": [],
                    "offerings": [],
                    "registrations": [],
                },
                status=status.HTTP_200_OK,
            )

        students = students_for_scope(scope)
        offerings = offerings_for_scope(scope)
        registrations = CourseRegistration.objects.select_related(
            "student",
            "student__user",
            "offering",
            "offering__course",
            "offering__semester",
            "tutorial_group",
            "lab_group",
        ).filter(student__in=students)
        return Response(
            {
                "title": "Manage Students",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
                "students": [serialize_student(student) for student in students],
                "offerings": [serialize_offering(offering) for offering in offerings],
                "registrations": CourseRegistrationSerializer(
                    registrations.order_by("-created_at"),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        student = students_for_scope(scope).filter(pk=request.data.get("student_id")).first()
        if not student:
            return Response({"detail": "Student not found in this executive scope."}, status=status.HTTP_404_NOT_FOUND)
        offering = offerings_for_scope(scope).filter(pk=request.data.get("offering_id")).first()
        if not offering:
            return Response({"detail": "Course offering not found in this executive scope."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "add")).strip().lower()
        if action == "drop":
            registration, error, response_status = drop_student_course(
                student=student,
                offering=offering,
                actor=profile,
                manual=True,
                decision_note=str(request.data.get("decision_note", "")).strip(),
            )
            message = "Course dropped for student."
        else:
            registration, error, response_status = register_student(
                student=student,
                offering=offering,
                actor=profile,
                tutorial_group_id=request.data.get("tutorial_group_id"),
                tutorial_group_code=request.data.get("tutorial_group_code"),
                lab_group_id=request.data.get("lab_group_id"),
                lab_group_code=request.data.get("lab_group_code"),
                request_note=str(request.data.get("request_note", "")).strip(),
                manual=True,
                allow_credit_override=_parse_bool(request.data.get("allow_credit_override")),
                allow_capacity_override=_parse_bool(request.data.get("allow_capacity_override")),
            )
            message = "Course added for student."
        if error:
            return Response({"detail": error}, status=response_status)
        return Response(
            {
                "message": message,
                "registration": CourseRegistrationSerializer(registration).data,
            },
            status=response_status,
        )

    def patch(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not scope_supports_academic_workflows(scope):
            return Response(non_academic_scope_response(scope), status=status.HTTP_403_FORBIDDEN)

        registration = (
            CourseRegistration.objects.select_related("offering", "offering__course")
            .filter(pk=request.query_params.get("registration_id"), student__in=students_for_scope(scope))
            .first()
        )
        if not registration:
            return Response({"detail": "Course registration not found."}, status=status.HTTP_404_NOT_FOUND)

        error, response_status = change_registered_group(
            registration=registration,
            tutorial_group_id=request.data.get("tutorial_group_id"),
            tutorial_group_code=request.data.get("tutorial_group_code"),
            lab_group_id=request.data.get("lab_group_id"),
            lab_group_code=request.data.get("lab_group_code"),
            allow_capacity_override=_parse_bool(request.data.get("allow_capacity_override")),
        )
        if error:
            return Response({"detail": error}, status=response_status)
        registration.refresh_from_db()
        return Response(
            {
                "message": "Student course group changed successfully.",
                "registration": CourseRegistrationSerializer(registration).data,
            },
            status=status.HTTP_200_OK,
        )
