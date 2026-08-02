from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole
from technician_app.models import Technician


def _technician_rows():
    profiles = (
        models.Profile.objects.select_related(
            "user", "technician_detail", "technician_detail__department"
        )
        .filter(role=models.Profile.ROLE_TECHNICIAN)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    rows = []
    for profile in profiles:
        try:
            detail = profile.technician_detail
        except Technician.DoesNotExist:
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
                "department_name": profile.department.name if profile.department_id else "",
                "specialization": detail.specialization if detail else "",
                "is_active": bool(profile.is_active and profile.user.is_active),
            }
        )
    return rows


class AdminManageTechnicians(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _technician_rows()
        return Response(
            {
                "title": "Manage Technicians",
                "section": "admin",
                "summary": {
                    "total": len(rows),
                    "active": sum(1 for row in rows if row["is_active"]),
                },
                "technicians": rows,
            }
        )

    def patch(self, request):
        profile = models.Profile.objects.select_related("user").filter(
            pk=request.query_params.get("profile_id"),
            role=models.Profile.ROLE_TECHNICIAN,
        ).first()
        if not profile:
            return Response({"detail": "Technician not found."}, status=status.HTTP_404_NOT_FOUND)

        department = models.Department.objects.filter(code="ICT", is_active=True).first()
        if not department:
            return Response(
                {"detail": "The standalone ICT department must exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.school = None
        profile.center = None
        profile.unit = None
        profile.department = department
        for field in ("staff_id", "designation", "phone"):
            if field in request.data:
                setattr(profile, field, str(request.data.get(field) or "").strip())
        if "is_active" in request.data:
            profile.is_active = bool(request.data.get("is_active"))
            profile.user.is_active = profile.is_active
            profile.user.save(update_fields=["is_active"])
        profile.save()

        detail, _created = Technician.objects.get_or_create(profile=profile)
        detail.staff_id = profile.staff_id
        detail.designation = profile.designation
        detail.is_active = profile.is_active
        if "specialization" in request.data:
            detail.specialization = str(request.data.get("specialization") or "").strip()
        detail.save()
        return Response({"message": "Technician account updated successfully."})


__all__ = ["AdminManageTechnicians"]
