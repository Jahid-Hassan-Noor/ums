from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole
from caterer_app.models import Caterer


def _caterer_rows():
    profiles = (
        models.Profile.objects.select_related(
            "user", "caterer_detail", "caterer_detail__center", "caterer_detail__unit"
        )
        .filter(role=models.Profile.ROLE_CATERER)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    rows = []
    for profile in profiles:
        try:
            detail = profile.caterer_detail
        except Caterer.DoesNotExist:
            detail = None
        rows.append(
            {
                "id": profile.id,
                "username": profile.user.username,
                "name": f"{profile.user.first_name} {profile.user.last_name}".strip() or profile.user.username,
                "email": profile.user.email,
                "staff_id": detail.caterer_id if detail else "",
                "designation": detail.designation if detail else "",
                "phone": profile.phone,
                "center_name": detail.center.name if detail and detail.center_id else "",
                "unit_name": detail.unit.name if detail and detail.unit_id else "",
                "canteen_location": detail.canteen_location if detail else "",
                "is_active": bool(profile.is_active and profile.user.is_active),
            }
        )
    return rows


class AdminManageCaterers(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _caterer_rows()
        return Response(
            {
                "title": "Manage Caterers",
                "section": "admin",
                "summary": {
                    "total": len(rows),
                    "active": sum(1 for row in rows if row["is_active"]),
                },
                "caterers": rows,
            }
        )

    def patch(self, request):
        profile = models.Profile.objects.select_related("user").filter(
            pk=request.query_params.get("profile_id"),
            role=models.Profile.ROLE_CATERER,
        ).first()
        if not profile:
            return Response({"detail": "Caterer not found."}, status=status.HTTP_404_NOT_FOUND)

        center = models.Center.objects.filter(code="CSAA", is_active=True).first()
        unit = models.Unit.objects.filter(code="CTN-ADMIN", is_active=True).first()
        if not center or not unit:
            return Response(
                {"detail": "The CSAA centre and CTN-ADMIN unit must exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "phone" in request.data:
            profile.phone = str(request.data.get("phone") or "").strip()
        if "is_active" in request.data:
            profile.is_active = bool(request.data.get("is_active"))
            profile.user.is_active = profile.is_active
            profile.user.save(update_fields=["is_active"])
        profile.save()

        detail, _created = Caterer.objects.get_or_create(profile=profile)
        detail.center = center
        detail.unit = unit
        detail.school = None
        detail.department = unit.department
        if "staff_id" in request.data:
            detail.caterer_id = str(request.data.get("staff_id") or "").strip()
        if "designation" in request.data:
            detail.designation = str(request.data.get("designation") or "").strip()
        detail.is_active = profile.is_active
        if "canteen_location" in request.data:
            detail.canteen_location = str(request.data.get("canteen_location") or "").strip()
        detail.save()
        return Response({"message": "Caterer account updated successfully."})


__all__ = ["AdminManageCaterers"]
