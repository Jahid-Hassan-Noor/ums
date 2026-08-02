from django.contrib import admin

from auth_app.models import Admin, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


@admin.register(Admin)
class AuthAdminProfileAdmin(admin.ModelAdmin):
    list_display = ("profile", "admin_id", "designation", "is_active")
    search_fields = ("profile__user__username", "profile__user__email", "admin_id")
