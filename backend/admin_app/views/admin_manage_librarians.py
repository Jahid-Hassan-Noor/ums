from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from admin_app.role_config import resolve_role_ownership_from_payload
from auth_app.permissions import IsAdminRole
from librarian_app.models import Librarian


def _librarian_rows():
    profiles = (
        models.Profile.objects.select_related(
            "user", "librarian_detail", "librarian_detail__center", "librarian_detail__unit"
        )
        .filter(role=models.Profile.ROLE_LIBRARIAN)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    rows = []
    for profile in profiles:
        try:
            detail = profile.librarian_detail
        except Librarian.DoesNotExist:
            detail = None
        rows.append(
            {
                "id": profile.id,
                "username": profile.user.username,
                "name": f"{profile.user.first_name} {profile.user.last_name}".strip() or profile.user.username,
                "email": profile.user.email,
                "staff_id": profile.staff_id or (detail.staff_id if detail else ""),
                "designation": profile.designation or (detail.designation if detail else ""),
                "phone": profile.phone,
                "school_name": profile.school.name if profile.school_id else "",
                "center_name": profile.center.name if profile.center_id else "",
                "unit_name": profile.unit.name if profile.unit_id else "",
                "department_name": profile.department.name if profile.department_id else "",
                "office_location": detail.office_location if detail else "",
                "is_active": bool(profile.is_active and profile.user.is_active),
            }
        )
    return rows


class AdminManageLibrarians(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _librarian_rows()
        return Response(
            {
                "title": "Manage Librarians",
                "section": "admin",
                "summary": {
                    "total": len(rows),
                    "active": sum(1 for row in rows if row["is_active"]),
                },
                "librarians": rows,
            }
        )

    def patch(self, request):
        profile = models.Profile.objects.select_related("user").filter(
            pk=request.query_params.get("profile_id"),
            role=models.Profile.ROLE_LIBRARIAN,
        ).first()
        if not profile:
            return Response({"detail": "Librarian not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            ownership = resolve_role_ownership_from_payload(
                models.Profile.ROLE_LIBRARIAN,
                request.data,
                current_profile=profile,
            )
        except ValidationError as error:
            return Response(
                getattr(error, "message_dict", {"detail": str(error)}),
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.school = ownership["school"]
        profile.center = ownership["center"]
        profile.unit = ownership["unit"]
        profile.department = ownership["department"]
        for field in ("staff_id", "designation", "phone"):
            if field in request.data:
                setattr(profile, field, str(request.data.get(field) or "").strip())
        if "is_active" in request.data:
            profile.is_active = bool(request.data.get("is_active"))
            profile.user.is_active = profile.is_active
            profile.user.save(update_fields=["is_active"])
        profile.save()

        detail, _created = Librarian.objects.get_or_create(profile=profile)
        detail.staff_id = profile.staff_id
        detail.designation = profile.designation
        detail.school = profile.school
        detail.center = profile.center
        detail.unit = profile.unit
        detail.department = profile.department
        detail.is_active = profile.is_active
        if "office_location" in request.data:
            detail.office_location = str(request.data.get("office_location") or "").strip()
        detail.save()
        return Response({"message": "Librarian account updated successfully."})


__all__ = ["AdminManageLibrarians"]
