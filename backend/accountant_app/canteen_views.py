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
    dashboard_summary,
    ensure_account,
    find_student,
    initialize_accounts,
    normalize_month,
    setting,
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


class AccountantCanteen(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
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
                "title": "Accountant Canteen Allowance",
                "section": "accountant",
                "current": dashboard_summary(),
                "settings": {
                    "monthly_allowance": str(setting().monthly_allowance),
                    "current_allocation": str(allocation_for_month(current_month)),
                    "eligible_students": active_students().count(),
                },
                "bonuses": [
                    _bonus_payload(item)
                    for item in CanteenMonthlyBonus.objects.all()[:24]
                ],
            }
        )

    def post(self, request):
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
                "message": "Student canteen balance added successfully.",
                "account": account_payload(account),
            },
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        config = setting()
        changes = []
        event_data = {}
        try:
            if "monthly_allowance" in request.data:
                config.monthly_allowance = Decimal(str(request.data.get("monthly_allowance")))
                config.updated_by = request.user.profile
                config.save()
                changes.append("monthly allowance")
                event_data["monthly_allowance"] = str(config.monthly_allowance)

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
        return Response({"message": "Canteen allowance settings updated successfully."})


__all__ = ["AccountantCanteen"]
