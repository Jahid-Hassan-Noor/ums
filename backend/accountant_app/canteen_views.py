from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsAccountantRole
from caterer_app.models import CanteenMonthlyBonus
from caterer_app.notifications import notify_allowance_policy_updated, notify_balance_adjusted
from caterer_app.service import (
    account_payload,
    add_balance,
    active_students,
    allocation_for_month,
    allowance_month,
    canteen_module_enabled,
    dashboard_summary,
    dining_label,
    ensure_account,
    find_student,
    initialize_accounts,
    module_unavailable_message,
    normalize_month,
    monthly_allowance_amount,
    policy_payload,
    update_monthly_allowance,
)


def _bonus_payload(bonus):
    return {
        "month": bonus.month.isoformat(),
        "extra_amount": str(bonus.extra_amount),
        "occasion": bonus.occasion,
    }


def _validation_detail(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    if hasattr(error, "messages"):
        return {"detail": "; ".join(error.messages)}
    return {"detail": str(error)}


def _module_unavailable_response():
    return Response({"detail": module_unavailable_message()}, status=status.HTTP_404_NOT_FOUND)


class AccountantCanteen(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        if not canteen_module_enabled():
            return _module_unavailable_response()
        student_id = request.query_params.get("student_id")
        if student_id:
            student = find_student(student_id)
            if not student:
                return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
            try:
                account = ensure_account(student)
            except ValidationError as error:
                return Response(_validation_detail(error), status=status.HTTP_400_BAD_REQUEST)
            return Response({"account": account_payload(account)})

        current_month = allowance_month()
        return Response(
            {
                "title": f"Accountant {dining_label()} Allowance",
                "section": "accountant",
                "current": dashboard_summary(),
                "settings": {
                    "monthly_allowance": str(monthly_allowance_amount()),
                    "current_allocation": str(allocation_for_month(current_month)),
                    "eligible_students": active_students().count(),
                    "policy": policy_payload(),
                },
                "bonuses": [
                    _bonus_payload(item)
                    for item in CanteenMonthlyBonus.objects.all()[:24]
                ],
            }
        )

    def post(self, request):
        if not canteen_module_enabled():
            return _module_unavailable_response()
        student = find_student(request.data.get("student_id"))
        if not student:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            account, adjustment = add_balance(
                student=student,
                admin_profile=request.user.profile,
                amount=request.data.get("amount"),
                reason=request.data.get("reason"),
            )
        except ValidationError as error:
            return Response(_validation_detail(error), status=status.HTTP_400_BAD_REQUEST)
        notify_balance_adjusted(student, adjustment, account, request.user.profile)
        return Response(
            {
                "message": f"Student {dining_label().lower()} balance added successfully.",
                "account": account_payload(account),
            },
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        if not canteen_module_enabled():
            return _module_unavailable_response()
        changes = []
        event_data = {}
        try:
            if "monthly_allowance" in request.data:
                allowance = update_monthly_allowance(
                    request.data.get("monthly_allowance"),
                    request.user.profile,
                )
                changes.append("monthly allowance")
                event_data["monthly_allowance"] = str(allowance)

            if "month" in request.data:
                month = normalize_month(request.data.get("month"))
                extra_amount = Decimal(str(request.data.get("extra_amount", "0")))
                occasion = str(request.data.get("occasion") or "").strip()
                bonus, _created = CanteenMonthlyBonus.objects.get_or_create(month=month)
                bonus.extra_amount = extra_amount
                bonus.occasion = occasion
                bonus.updated_by = request.user.profile
                bonus.save()
                initialize_accounts(month)
                changes.append("monthly bonus")
                event_data.update(
                    {
                        "month": month.isoformat(),
                        "extra_amount": str(bonus.extra_amount),
                        "occasion": bonus.occasion,
                    }
                )

            initialize_accounts()
        except (ValidationError, ArithmeticError, ValueError) as error:
            detail = _validation_detail(error)
            if detail == {"detail": str(error)}:
                detail = {"detail": "Provide valid allowance amounts."}
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)
        if changes:
            notify_allowance_policy_updated(
                actor=request.user.profile,
                changes=changes,
                data=event_data,
            )
        return Response({"message": f"{dining_label()} allowance settings updated successfully."})


__all__ = ["AccountantCanteen"]
