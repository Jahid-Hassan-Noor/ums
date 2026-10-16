from django.urls import path

from hr_app.onboarding_views import (
    HrOnboardingBoard,
    HrOnboardingCardEmployeeLink,
    HrOnboardingCardHistory,
    HrOnboardingCardMove,
    HrOnboardingCards,
    HrOnboardingColumnDetail,
    HrOnboardingColumns,
)
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
    path("onboarding-board", HrOnboardingBoard.as_view()),
    path("onboarding-board/cards", HrOnboardingCards.as_view()),
    path("onboarding-board/cards/<int:card_id>/move", HrOnboardingCardMove.as_view()),
    path("onboarding-board/cards/<int:card_id>/employee-link", HrOnboardingCardEmployeeLink.as_view()),
    path("onboarding-board/cards/<int:card_id>/history", HrOnboardingCardHistory.as_view()),
    path("onboarding-board/columns", HrOnboardingColumns.as_view()),
    path("onboarding-board/columns/<int:column_id>", HrOnboardingColumnDetail.as_view()),
]
