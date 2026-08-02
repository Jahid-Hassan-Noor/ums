from django.contrib import admin

from caterer_app.models import (
    CanteenBalanceAdjustment,
    Caterer,
    CanteenMonthlyBonus,
    CanteenSetting,
    CanteenTransaction,
    StudentCanteenAccount,
)


admin.site.register(Caterer)
admin.site.register(CanteenBalanceAdjustment)
admin.site.register(CanteenMonthlyBonus)
admin.site.register(CanteenSetting)
admin.site.register(CanteenTransaction)
admin.site.register(StudentCanteenAccount)
