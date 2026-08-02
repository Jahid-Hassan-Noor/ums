from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accountant_app.models import Accountant
from admin_app import models
from auth_app.permissions import IsAdminRole


def _accountant_rows():
    profiles = (
        models.Profile.objects.select_related("user", "accountant_detail")
        .filter(role=models.Profile.ROLE_ACCOUNTANT)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    rows = []
    for profile in profiles:
        try:
            detail = profile.accountant_detail
        except Accountant.DoesNotExist:
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
                "office_location": detail.office_location if detail else "",
                "is_active": bool(profile.is_active and profile.user.is_active),
            }
        )
    return rows


class AdminManageAccountants(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _accountant_rows()
        return Response(
            {
                "title": "Manage Accountants",
                "section": "admin",
                "summary": {
                    "total": len(rows),
                    "active": sum(1 for row in rows if row["is_active"]),
                },
                "accountants": rows,
            }
        )

    def patch(self, request):
        profile = models.Profile.objects.select_related("user").filter(
            pk=request.query_params.get("profile_id"),
            role=models.Profile.ROLE_ACCOUNTANT,
        ).first()
        if not profile:
            return Response({"detail": "Accountant not found."}, status=status.HTTP_404_NOT_FOUND)

        for field in ("staff_id", "designation", "phone"):
            if field in request.data:
                setattr(profile, field, str(request.data.get(field) or "").strip())
        if "is_active" in request.data:
            profile.is_active = bool(request.data.get("is_active"))
            profile.user.is_active = profile.is_active
            profile.user.save(update_fields=["is_active"])
        profile.save()

        detail, _created = Accountant.objects.get_or_create(profile=profile)
        detail.accountant_id = profile.staff_id
        detail.designation = profile.designation
        detail.is_active = profile.is_active
        if "office_location" in request.data:
            detail.office_location = str(request.data.get("office_location") or "").strip()
        detail.save()
        return Response({"message": "Accountant account updated successfully."})


__all__ = ["AdminManageAccountants"]
