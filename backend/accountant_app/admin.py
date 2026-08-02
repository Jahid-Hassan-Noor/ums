from django.contrib import admin

from accountant_app.models import (
    Accountant,
    Fine,
    FinanceGatewayConfig,
    PaymentAttempt,
    Subscription,
    SubscriptionPlan,
)


admin.site.register(Accountant)
admin.site.register(FinanceGatewayConfig)
admin.site.register(PaymentAttempt)
admin.site.register(Subscription)
admin.site.register(SubscriptionPlan)


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "reason", "amount", "currency", "status", "due_date", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("reason", "student__user__username", "student__user__first_name", "student__user__last_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "paid_at", "deducted_at")

