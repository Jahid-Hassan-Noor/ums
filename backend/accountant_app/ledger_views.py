from django.core.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accountant_app.ledger_service import (
    audit_trail,
    category_payload,
    charge_payload,
    create_bulk_charge,
    create_fee_category,
    create_payment_plan,
    create_student_charge,
    dashboard_summary,
    holds_filtered,
    hold_payload,
    installment_payload,
    payment_plan_payload,
    place_finance_hold,
    record_plan_payment,
    release_finance_hold,
    student_balance_summaries_paginated,
    student_charges_filtered,
    student_finance_summary,
    student_ledger_entries,
)
from accountant_app.models import FeeCategory, PaymentPlan, PaymentPlanInstallment, StudentFinanceHold
from admin_app.models import Profile
from auth_app.permissions import IsAccountantRole, IsActiveUmsUser


def validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(error, "messages"):
        return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class FinanceFeeCategories(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        categories = FeeCategory.objects.order_by("name", "code")
        return Response({"categories": [category_payload(category) for category in categories]})

    def post(self, request):
        try:
            category = create_fee_category(data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Fee category saved.", "category": category_payload(category)}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        try:
            category = create_fee_category(data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Fee category updated.", "category": category_payload(category)})


class FinanceStudentLedgers(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        student_id = request.query_params.get("student_id")
        if student_id:
            student = Profile.objects.select_related("user").filter(pk=student_id, role=Profile.ROLE_STUDENT).first()
            if not student:
                return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(student_finance_summary(student))
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        return Response(student_balance_summaries_paginated(
            query=request.query_params.get("q"),
            sort_by=request.query_params.get("sort"),
            page=page,
            page_size=page_size,
        ))

    def post(self, request):
        try:
            charge = create_student_charge(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Student charge posted.", "charge": charge_payload(charge)}, status=status.HTTP_201_CREATED)


class FinanceStudentBalance(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request, student_id):
        profile = request.user.profile
        if profile.role == Profile.ROLE_STUDENT and profile.id != student_id:
            return Response({"detail": "You can only view your own student ledger."}, status=status.HTTP_403_FORBIDDEN)
        if profile.role not in {Profile.ROLE_STUDENT, Profile.ROLE_ACCOUNTANT, Profile.ROLE_ADMIN}:
            return Response({"detail": "You cannot access student finance balances."}, status=status.HTTP_403_FORBIDDEN)
        student = Profile.objects.select_related("user").filter(pk=student_id, role=Profile.ROLE_STUDENT).first()
        if not student:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(student_finance_summary(student))


class FinanceHolds(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        is_active = None
        if "active" in request.query_params:
            is_active = request.query_params.get("active") != "false"
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        return Response(holds_filtered(
            query=request.query_params.get("q"),
            is_active=is_active,
            page=page,
            page_size=page_size,
        ))

    def post(self, request):
        try:
            hold = place_finance_hold(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Finance hold placed.", "hold": hold_payload(hold)}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        try:
            hold = release_finance_hold(actor=request.user.profile, hold_id=request.data.get("hold_id"))
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Finance hold released.", "hold": hold_payload(hold)})


class FinanceDashboard(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        return Response(dashboard_summary())


class FinanceAuditTrail(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        return Response(audit_trail(
            query=request.query_params.get("q"),
            entry_type=request.query_params.get("entry_type"),
            student_id=request.query_params.get("student_id"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
            page=page,
            page_size=page_size,
        ))


class FinanceBulkCharge(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request):
        try:
            result = create_bulk_charge(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": f"{result['posted_count']} charges posted.", **result}, status=status.HTTP_201_CREATED)


class FinancePaymentPlans(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        student_id = request.query_params.get("student_id")
        plans = PaymentPlan.objects.select_related("student", "student__user").all()
        if student_id:
            plans = plans.filter(student_id=student_id)
        status_filter = request.query_params.get("status")
        if status_filter:
            plans = plans.filter(status=status_filter)
        plans = plans.order_by("-created_at")[:100]
        return Response({"plans": [payment_plan_payload(plan) for plan in plans]})

    def post(self, request):
        try:
            plan = create_payment_plan(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Payment plan created.", "plan": payment_plan_payload(plan)}, status=status.HTTP_201_CREATED)


class FinancePaymentPlanDetail(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request, plan_id):
        plan = PaymentPlan.objects.select_related("student", "student__user").filter(pk=plan_id).first()
        if not plan:
            return Response({"detail": "Payment plan not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(payment_plan_payload(plan))

    def patch(self, request, plan_id):
        plan = PaymentPlan.objects.filter(pk=plan_id).first()
        if not plan:
            return Response({"detail": "Payment plan not found."}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get("status")
        if new_status in dict(PaymentPlan.STATUS_CHOICES):
            plan.status = new_status
            plan.save(update_fields=["status"])
        return Response({"message": "Payment plan updated.", "plan": payment_plan_payload(plan)})

    def delete(self, request, plan_id):
        plan = PaymentPlan.objects.filter(pk=plan_id).first()
        if not plan:
            return Response({"detail": "Payment plan not found."}, status=status.HTTP_404_NOT_FOUND)
        if plan.status == PaymentPlan.STATUS_ACTIVE:
            plan.status = PaymentPlan.STATUS_CANCELLED
            plan.save(update_fields=["status"])
            PaymentPlanInstallment.objects.filter(plan=plan, status=PaymentPlanInstallment.STATUS_PENDING).update(
                status=PaymentPlanInstallment.STATUS_CANCELLED
            )
        return Response({"message": "Payment plan cancelled."})


class FinancePaymentPlanPay(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, plan_id):
        try:
            plan = record_plan_payment(actor=request.user.profile, plan_id=plan_id, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Installment payment recorded.", "plan": payment_plan_payload(plan)})


class FinanceStudentLedgerEntries(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request, student_id):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        return Response(student_ledger_entries(
            student_id=student_id,
            page=page,
            page_size=page_size,
            entry_type=request.query_params.get("entry_type"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        ))


class FinanceStudentCharges(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request, student_id):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        return Response(student_charges_filtered(
            student_id=student_id,
            page=page,
            page_size=page_size,
            status=request.query_params.get("status"),
            category_id=request.query_params.get("category_id"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        ))
