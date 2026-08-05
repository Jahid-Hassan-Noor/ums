from rest_framework.permissions import BasePermission

from admin_app.settings_registry import features_enabled_for_path
from auth_app.models import Profile


def profile_role_for_user(user):
    if not user or not user.is_authenticated or not user.is_active:
        return None

    profile = Profile.objects.filter(user=user).only("role", "is_active").first()
    if profile:
        # Admin role should be allowed even if the profile is inactive.
        if profile.role == Profile.ROLE_ADMIN:
            return Profile.ROLE_ADMIN
        return profile.role if profile.is_active else None

    if user.is_staff or user.is_superuser:
        return Profile.ROLE_ADMIN

    return None


class HasProfileRole(BasePermission):
    allowed_roles = set()

    def has_permission(self, request, view):
        role = profile_role_for_user(request.user)
        return role in self.allowed_roles and features_enabled_for_path(
            request.path,
            role=role,
        )


class IsActiveUmsUser(HasProfileRole):
    allowed_roles = {role for role, _label in Profile.ROLE_CHOICES}


class IsStudentRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_STUDENT}


class IsTeacherRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_TEACHER}


class IsExecutiveRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_EXECUTIVE}


class IsLibrarianRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_LIBRARIAN}


class IsCatererRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_CATERER}


class IsTechnicianRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_TECHNICIAN}


class IsAccountantRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_ACCOUNTANT}


class IsHrRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_HR}


class IsAdminRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_ADMIN}


class IsApplicantRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_APPLICANT}


class IsApplicantStaffRole(HasProfileRole):
    allowed_roles = {Profile.ROLE_ADMIN, Profile.ROLE_EXECUTIVE}
