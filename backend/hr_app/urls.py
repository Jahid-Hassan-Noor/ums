from django.urls import path

from hr_app.views import (
    HrCompensationRequests,
    HrDashboard,
    HrEmployeeCompensationRequests,
    HrEmployeeDetail,
    HrEmployeeSalaryAdjustments,
    HrEmployees,
    HrMyProfile,
    HrPositions,
    HrProfiles,
    HrStaffAccounts,
    HrStatistics,
    HrUms,
)


urlpatterns = [
    path("", HrUms.as_view()),
    path("dashboard", HrDashboard.as_view()),
    path("statistics", HrStatistics.as_view()),
    path("employees", HrEmployees.as_view()),
    path("employees/<int:employee_id>", HrEmployeeDetail.as_view()),
    path("employees/<int:employee_id>/compensation-requests", HrEmployeeCompensationRequests.as_view()),
    path("employees/<int:employee_id>/salary-adjustments", HrEmployeeSalaryAdjustments.as_view()),
    path("compensation-requests", HrCompensationRequests.as_view()),
    path("my-profile", HrMyProfile.as_view()),
    path("positions", HrPositions.as_view()),
    path("profiles", HrProfiles.as_view()),
    path("staff-accounts", HrStaffAccounts.as_view()),
]
