from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models as admin_models
from auth_app.permissions import IsExecutiveRole
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    scope_payload,
)
from executive_app.models import Executive
from teacher_app.models import Teacher


EDITABLE_PROFILE_FIELDS = {"designation", "phone"}
EDITABLE_TEACHER_FIELDS = {"designation", "academic_rank", "specialization", "office_location"}
EDITABLE_EXECUTIVE_FIELDS = {"designation", "office_location", "responsibility_area"}


def staff_for_scope(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return admin_models.Profile.objects.none()
    relation = "school" if kind == "school" else "center"
    scope_filter = (
        Q(**{f"teacher_detail__{relation}": unit})
        | Q(**{f"teacher_detail__unit__{relation}": unit})
        | Q(**{f"teacher_scope_assignments__{relation}": unit})
        | Q(**{f"executive_detail__{relation}": unit})
        | Q(**{f"executive_detail__unit__{relation}": unit})
    )
    return (
        admin_models.Profile.objects.select_related(
            "user",
            "teacher_detail",
            "teacher_detail__school",
            "teacher_detail__center",
            "executive_detail",
            "executive_detail__school",
            "executive_detail__center",
        )
        .filter(
            Q(role=admin_models.Profile.ROLE_TEACHER) | Q(role=admin_models.Profile.ROLE_EXECUTIVE),
            is_active=True,
        )
        .filter(scope_filter)
        .distinct()
        .order_by("role", "user__first_name", "user__last_name")
    )


def serialize_staff(profile):
    user = profile.user
    detail = {}
    if profile.role == admin_models.Profile.ROLE_TEACHER:
        teacher = getattr(profile, "teacher_detail", None)
        if teacher:
            detail = {
                "academic_rank": teacher.academic_rank,
                "specialization": teacher.specialization,
                "office_location": teacher.office_location,
            }
    if profile.role == admin_models.Profile.ROLE_EXECUTIVE:
        executive = getattr(profile, "executive_detail", None)
        if executive:
            detail = {
                "office_location": executive.office_location,
                "responsibility_area": executive.responsibility_area,
            }
    return {
        "id": profile.id,
        "role": profile.role,
        "name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "username": user.username,
        "email": user.email,
        "staff_id": profile.staff_id,
        "designation": profile.designation,
        "phone": profile.phone,
        "school": profile.school.code if profile.school_id else "",
        "center": profile.center.code if profile.center_id else "",
        "details": detail,
    }


class ExecutiveManageTeachers(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
            scope_error = None
        except ValueError as exc:
            scope = {"kind": None, "unit": None}
            scope_error = str(exc)
        staff = staff_for_scope(scope)
        return Response(
            {
                "title": "Manage Teachers & Staff",
                "section": "executive",
                "scope": scope_payload(scope),
                "scope_error": scope_error,
                "members": [serialize_staff(member) for member in staff],
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        profile = get_executive_profile(request.user)
        try:
            scope = get_executive_scope(profile)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        member = staff_for_scope(scope).filter(pk=request.query_params.get("profile_id")).first()
        if not member:
            return Response({"detail": "Teacher or staff member not found in this executive scope."}, status=status.HTTP_404_NOT_FOUND)

        profile_updates = []
        for field in EDITABLE_PROFILE_FIELDS:
            if field in request.data:
                setattr(member, field, str(request.data.get(field, "")).strip())
                profile_updates.append(field)
        if profile_updates:
            member.save(update_fields=profile_updates + ["updated_at"])

        if member.role == admin_models.Profile.ROLE_TEACHER:
            detail, _created = Teacher.objects.get_or_create(profile=member)
            detail_updates = []
            for field in EDITABLE_TEACHER_FIELDS:
                if field in request.data:
                    setattr(detail, field, str(request.data.get(field, "")).strip())
                    detail_updates.append(field)
            if detail_updates:
                detail.save(update_fields=detail_updates + ["updated_at"])

        if member.role == admin_models.Profile.ROLE_EXECUTIVE:
            detail, _created = Executive.objects.get_or_create(profile=member)
            detail_updates = []
            for field in EDITABLE_EXECUTIVE_FIELDS:
                if field in request.data:
                    setattr(detail, field, str(request.data.get(field, "")).strip())
                    detail_updates.append(field)
            if detail_updates:
                detail.save(update_fields=detail_updates + ["updated_at"])

        member.refresh_from_db()
        return Response(
            {
                "message": "Staff details updated successfully.",
                "member": serialize_staff(member),
            },
            status=status.HTTP_200_OK,
        )
