"""API views for the Fine/Charge feature."""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accountant_app.fine_service import (
    create_fine,
    deduct_fine_from_meal_allowance,
    fine_payload,
    list_fines_for_accountant,
    list_fines_for_student,
)
from accountant_app.models import Fine
from admin_app.models import Profile
from auth_app.permissions import IsAccountantRole, IsActiveUmsUser


def _validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(error, "messages"):
        return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class AccountantFineList(APIView):
    """
    GET  /finance/fines              – accountant: list all fines (filter by status)
    POST /finance/fines              – accountant: create a new fine
    """
    permission_classes = [IsAccountantRole]

    def get(self, request):
        status_filter = request.query_params.get("status")
        student_id = request.query_params.get("student_id")
        qs = list_fines_for_accountant(status_filter=status_filter, student_id=student_id)
        return Response({"fines": [fine_payload(f) for f in qs[:200]]})

    def post(self, request):
        data = request.data
        student_id = data.get("student_id")
        reason = (data.get("reason") or "").strip()
        amount = data.get("amount")
        description = (data.get("description") or "").strip()
        due_date_str = data.get("due_date")

        if not student_id:
            return Response({"detail": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not reason:
            return Response({"detail": "reason is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not amount:
            return Response({"detail": "amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve student profile
        student_profile = Profile.objects.filter(pk=student_id, role=Profile.ROLE_STUDENT).first()
        if not student_profile:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        # Resolve accountant
        accountant = getattr(request.user.profile, "accountant_detail", None)
        if accountant is None:
            return Response({"detail": "Accountant record not found."}, status=status.HTTP_403_FORBIDDEN)

        due_date = None
        if due_date_str:
            due_date = parse_datetime(due_date_str)
            if due_date is None:
                return Response({"detail": "Invalid due_date format. Use ISO 8601 (e.g. 2026-07-10T23:59:00Z)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fine = create_fine(
                accountant=accountant,
                student_profile=student_profile,
                reason=reason,
                amount=amount,
                description=description,
                due_date=due_date,
                request=request,
            )
        except ValidationError as error:
            return _validation_response(error)

        return Response(
            {"message": "Fine created and student notified.", "fine": fine_payload(fine)},
            status=status.HTTP_201_CREATED,
        )


class AccountantFineDetail(APIView):
    """
    GET /finance/fines/<pk>          – accountant: view fine detail
    """
    permission_classes = [IsAccountantRole]

    def get(self, request, pk):
        fine = Fine.objects.select_related("student", "student__user", "issued_by", "issued_by__profile", "issued_by__profile__user").filter(pk=pk).first()
        if not fine:
            return Response({"detail": "Fine not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"fine": fine_payload(fine)})


class AccountantFineDeduct(APIView):
    """
    POST /finance/fines/<pk>/deduct  – accountant: manually mark fine as deducted from meal allowance
    """
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        note = (request.data.get("note") or "").strip()
        try:
            fine = deduct_fine_from_meal_allowance(
                fine_id=pk,
                accountant_profile=request.user.profile,
                note=note,
            )
        except ValidationError as error:
            return _validation_response(error)
        return Response(
            {"message": "Fine marked as deducted. Student has been notified.", "fine": fine_payload(fine)}
        )


class StudentFineList(APIView):
    """
    GET /finance/my-fines            – student: list own fines
    """
    permission_classes = [IsActiveUmsUser]

    def get(self, request):
        profile = request.user.profile
        if profile.role != Profile.ROLE_STUDENT:
            return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
        qs = list_fines_for_student(profile)
        return Response({"fines": [fine_payload(f) for f in qs[:100]]})


class StudentFineInitiatePayment(APIView):
    """
    POST /finance/my-fines/<pk>/pay  – student: (re-)request a payment link for a fine
    """
    permission_classes = [IsActiveUmsUser]

    def post(self, request, pk):
        from accountant_app.fine_service import _create_fine_payment_link

        profile = request.user.profile
        if profile.role != Profile.ROLE_STUDENT:
            return Response({"detail": "Only students can pay fines."}, status=status.HTTP_403_FORBIDDEN)

        fine = Fine.objects.select_related("student", "student__user").filter(pk=pk, student=profile).first()
        if not fine:
            return Response({"detail": "Fine not found."}, status=status.HTTP_404_NOT_FOUND)
        if fine.status in (Fine.STATUS_PAID, Fine.STATUS_DEDUCTED):
            return Response({"detail": f"This fine is already {fine.status}."}, status=status.HTTP_400_BAD_REQUEST)

        # Refresh checkout URL if empty
        checkout_url = fine.checkout_url
        if not checkout_url:
            checkout_url = _create_fine_payment_link(fine=fine, request=request)
            if checkout_url:
                Fine.objects.filter(pk=fine.pk).update(checkout_url=checkout_url)
                fine.checkout_url = checkout_url

        if not checkout_url:
            return Response({"detail": "Payment gateway is not configured. Please contact the Finance Office."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        fine.refresh_from_db()
        return Response({"checkout_url": checkout_url, "fine": fine_payload(fine)})


class AccountantStudentList(APIView):
    """
    GET /finance/students - list of all student profiles (for fine creation dropdown/search)
    """
    permission_classes = [IsAccountantRole]

    def get(self, request):
        students = Profile.objects.filter(role=Profile.ROLE_STUDENT, is_active=True).select_related("user", "student_detail")
        q = request.query_params.get("q")
        if q:
            students = students.filter(
                models.Q(user__first_name__icontains=q) |
                models.Q(user__last_name__icontains=q) |
                models.Q(user__username__icontains=q) |
                models.Q(student_detail__student_id__icontains=q)
            )
        data = []
        for s in students[:100]:
            name = s.user.get_full_name().strip() or s.user.username
            student_id = getattr(s, "student_detail", None)
            identifier = student_id.student_id if student_id else ""
            data.append({
                "id": s.pk,
                "name": name,
                "email": s.user.email,
                "identifier": identifier,
            })
        return Response({"students": data})

