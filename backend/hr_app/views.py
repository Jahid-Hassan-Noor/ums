from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import Profile
from auth_app.permissions import IsActiveUmsUser, IsHrRole
from hr_app.models import CompensationChangeRequest, Employee, HRStaff, Position
from hr_app.service import (
    compensation_request_payload,
    compensation_requests_payload,
    create_compensation_request,
    create_salary_adjustment,
    create_or_update_employee,
    create_or_update_position,
    dashboard_payload,
    employee_detail_payload,
    employee_payload,
    employee_profile_options,
    hr_statistics_payload,
    hr_staff_payload,
    position_payload,
)


def validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(error, "messages"):
        return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class HrUms(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        return Response({"title": "HR Portal", "section": "hr"})


class HrDashboard(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        return Response({"title": "Human Resources Dashboard", "section": "hr", **dashboard_payload()})


class HrStatistics(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        return Response({"title": "HR Statistics", "section": "hr", **hr_statistics_payload()})


class HrProfiles(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        return Response({"profiles": employee_profile_options()})


class HrPositions(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        positions = Position.objects.select_related("department", "unit").order_by("title", "code")
        return Response({"positions": [position_payload(position) for position in positions]})

    def post(self, request):
        try:
            position = create_or_update_position(data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Position saved.", "position": position_payload(position)}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        try:
            position = create_or_update_position(data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Position updated.", "position": position_payload(position)})


class HrEmployees(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        employees = Employee.objects.select_related(
            "profile",
            "profile__user",
            "position",
            "position__department",
            "position__unit",
            "reporting_manager",
            "reporting_manager__profile",
            "reporting_manager__profile__user",
        )
        status_filter = request.query_params.get("status")
        role_filter = request.query_params.get("role")
        position_filter = request.query_params.get("position_id")
        search = str(request.query_params.get("q") or "").strip()
        if status_filter:
            employees = employees.filter(employment_status=status_filter)
        if role_filter:
            employees = employees.filter(profile__role=role_filter)
        if position_filter:
            employees = employees.filter(position_id=position_filter)
        if search:
            employees = employees.filter(
                Q(profile__user__first_name__icontains=search)
                | Q(profile__user__last_name__icontains=search)
                | Q(profile__user__username__icontains=search)
                | Q(profile__user__email__icontains=search)
                | Q(employee_no__icontains=search)
                | Q(work_email__icontains=search)
            )
        return Response({"employees": [employee_payload(employee) for employee in employees[:200]]})

    def post(self, request):
        try:
            employee = create_or_update_employee(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Employee record saved.", "employee": employee_payload(employee)}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        try:
            employee = create_or_update_employee(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Employee record updated.", "employee": employee_payload(employee)})


class HrEmployeeDetail(APIView):
    permission_classes = [IsHrRole]

    def get(self, request, employee_id):
        employee = (
            Employee.objects.select_related(
                "profile",
                "profile__user",
                "position",
                "position__department",
                "position__unit",
                "reporting_manager",
                "reporting_manager__profile",
                "reporting_manager__profile__user",
            )
            .filter(pk=employee_id)
            .first()
        )
        if employee is None:
            return Response({"detail": "Employee record was not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"employee": employee_detail_payload(employee)})


class HrEmployeeSalaryAdjustments(APIView):
    permission_classes = [IsHrRole]

    def post(self, request, employee_id):
        try:
            adjustment = create_salary_adjustment(
                actor=request.user.profile,
                employee_id=employee_id,
                data=request.data,
            )
        except ValidationError as error:
            return validation_response(error)
        employee = Employee.objects.select_related(
            "profile",
            "profile__user",
            "position",
            "position__department",
            "position__unit",
            "reporting_manager",
            "reporting_manager__profile",
            "reporting_manager__profile__user",
        ).get(pk=employee_id)
        return Response(
            {
                "message": "Salary change request submitted for Accountant approval.",
                "request": compensation_request_payload(adjustment),
                "employee": employee_detail_payload(employee),
            },
            status=status.HTTP_201_CREATED,
        )


class HrEmployeeCompensationRequests(APIView):
    permission_classes = [IsHrRole]

    def post(self, request, employee_id):
        try:
            request_obj = create_compensation_request(
                actor=request.user.profile,
                employee_id=employee_id,
                data=request.data,
            )
        except ValidationError as error:
            return validation_response(error)
        employee = Employee.objects.select_related(
            "profile",
            "profile__user",
            "position",
            "position__department",
            "position__unit",
            "reporting_manager",
            "reporting_manager__profile",
            "reporting_manager__profile__user",
        ).get(pk=employee_id)
        return Response(
            {
                "message": "Compensation change request submitted for Accountant approval.",
                "request": compensation_request_payload(request_obj),
                "employee": employee_detail_payload(employee),
            },
            status=status.HTTP_201_CREATED,
        )


class HrCompensationRequests(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        status_value = request.query_params.get("status")
        if status_value and status_value not in dict(CompensationChangeRequest.STATUS_CHOICES):
            return Response({"detail": "Unsupported compensation request status."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(compensation_requests_payload(status_value=status_value))


class HrMyProfile(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request):
        employee = (
            Employee.objects.select_related(
                "profile",
                "profile__user",
                "position",
                "position__department",
                "position__unit",
                "reporting_manager",
                "reporting_manager__profile",
                "reporting_manager__profile__user",
            )
            .filter(profile=request.user.profile)
            .first()
        )
        if not employee:
            return Response({"employee": None})
        return Response({"employee": employee_payload(employee)})


class HrStaffAccounts(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        profiles = (
            Profile.objects.select_related("user", "hr_detail")
            .filter(role=Profile.ROLE_HR)
            .order_by("user__first_name", "user__last_name", "user__username")
        )
        rows = []
        for profile in profiles:
            try:
                detail = profile.hr_detail
            except HRStaff.DoesNotExist:
                detail = HRStaff(profile=profile)
            rows.append(hr_staff_payload(detail))
        return Response({"hr_staff": rows})
