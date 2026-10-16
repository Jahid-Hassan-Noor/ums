from django.urls import path

from accountant_app.fine_views import (
    AccountantFineDeduct,
    AccountantFineDetail,
    AccountantFineList,
    StudentFineInitiatePayment,
    StudentFineList,
    AccountantStudentList,
)
from accountant_app.views import (
    AccountantDashboard,
    AccountantUms,
    AccountantSubscriptions,
    FinanceGatewaySettings,
    FinancePlans,
    MySubscriptions,
    PaymentReturn,
    PaymentWebhook,
    SubscriptionCard,
    SubscriptionPurchase,
)
from accountant_app.canteen_views import AccountantCanteen
from accountant_app.hr_compensation_views import AccountantCompensationRequests
from accountant_app.ledger_views import (
    FinanceBulkCharge,
    FinanceDashboard,
    FinanceFeeCategories,
    FinanceHolds,
    FinancePaymentPlanDetail,
    FinancePaymentPlanPay,
    FinancePaymentPlans,
    FinanceStudentBalance,
    FinanceStudentCharges,
    FinanceStudentLedgerEntries,
    FinanceStudentLedgerExport,
    FinanceStudentLedgers,
    FinanceAuditTrail,
)


urlpatterns = [
    path("", AccountantUms.as_view()),
    path("dashboard", AccountantDashboard.as_view()),
    path("canteen", AccountantCanteen.as_view(), name="finance_canteen"),
    path("hr-compensation-requests", AccountantCompensationRequests.as_view(), name="finance_hr_compensation_requests"),
    path("gateway", FinanceGatewaySettings.as_view()),
    path("plans", FinancePlans.as_view()),
    path("my-subscriptions", MySubscriptions.as_view()),
    path("subscriptions", AccountantSubscriptions.as_view()),
    path("subscriptions/purchase", SubscriptionPurchase.as_view()),
    path("subscriptions/<int:pk>/card", SubscriptionCard.as_view()),
    path("fee-categories", FinanceFeeCategories.as_view(), name="finance_fee_categories"),
    path("student-ledgers", FinanceStudentLedgers.as_view(), name="finance_student_ledgers"),
    path("students/<int:student_id>/balance", FinanceStudentBalance.as_view(), name="finance_student_balance"),
    path("students/<int:student_id>/entries", FinanceStudentLedgerEntries.as_view(), name="finance_student_ledger_entries"),
    path("students/<int:student_id>/charges", FinanceStudentCharges.as_view(), name="finance_student_charges"),
    path("holds", FinanceHolds.as_view(), name="finance_holds"),
    path("ledger/dashboard", FinanceDashboard.as_view(), name="finance_ledger_dashboard"),
    path("ledger/audit", FinanceAuditTrail.as_view(), name="finance_ledger_audit"),
    path("ledger/export", FinanceStudentLedgerExport.as_view(), name="finance_ledger_export"),
    path("ledger/bulk-charge", FinanceBulkCharge.as_view(), name="finance_bulk_charge"),
    path("ledger/payment-plans", FinancePaymentPlans.as_view(), name="finance_payment_plans"),
    path("ledger/payment-plans/<int:plan_id>", FinancePaymentPlanDetail.as_view(), name="finance_payment_plan_detail"),
    path("ledger/payment-plans/<int:plan_id>/pay", FinancePaymentPlanPay.as_view(), name="finance_payment_plan_pay"),
    path("payments/return", PaymentReturn.as_view(), name="finance_payment_return"),
    path("payments/webhook", PaymentWebhook.as_view(), name="finance_payment_webhook"),
    # Fine / charge management
    path("students", AccountantStudentList.as_view(), name="finance_students_list"),
    path("fines", AccountantFineList.as_view(), name="finance_fine_list"),
    path("fines/<int:pk>", AccountantFineDetail.as_view(), name="finance_fine_detail"),
    path("fines/<int:pk>/deduct", AccountantFineDeduct.as_view(), name="finance_fine_deduct"),
    # Student fine endpoints
    path("my-fines", StudentFineList.as_view(), name="finance_student_fine_list"),
    path("my-fines/<int:pk>/pay", StudentFineInitiatePayment.as_view(), name="finance_student_fine_pay"),
]
