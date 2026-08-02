"""Shared profile helpers used across all apps.

These functions were previously duplicated in several service modules
(``student_app/registration_service.py``, ``teacher_app/assignment_service.py``,
``executive_app/course_schedule.py``, ``technician_app/*``). Centralizing them
removes the duplication and guarantees identical behaviour everywhere.
"""

from admin_app import models


def profile_display_name(profile):
    """Return a human-friendly display name for a ``Profile`` (``""`` if none)."""
    if not profile:
        return ""
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def profile_identifier(profile):
    """Return the most meaningful identifier for a ``Profile``.

    Prefers a student's ``student_id`` for student profiles, then falls back to
    ``staff_id`` / ``student_id`` / username.
    """
    if profile.role == models.Profile.ROLE_STUDENT:
        try:
            if profile.student_detail.student_id:
                return profile.student_detail.student_id
        except Exception:
            pass
    return profile.staff_id or profile.student_id or profile.user.username


def get_role_profile(user, role, select_related=None):
    """Return the active ``Profile`` for ``user`` scoped to ``role``, or ``None``."""
    if not user or not user.is_authenticated:
        return None
    queryset = models.Profile.objects
    if select_related:
        queryset = queryset.select_related(*select_related)
    return (
        queryset.filter(user=user, role=role, is_active=True)
        .first()
    )


_STUDENT_SELECT = (
    "user",
    "student_detail",
    "student_detail__school",
    "student_detail__center",
    "student_detail__program",
)
_TEACHER_SELECT = ("user",)
_EXECUTIVE_SELECT = (
    "user",
    "executive_detail",
    "executive_detail__school",
    "executive_detail__center",
    "executive_detail__unit",
    "executive_detail__unit__school",
    "executive_detail__unit__center",
)


def get_student_profile(user):
    return get_role_profile(
        user, models.Profile.ROLE_STUDENT, select_related=_STUDENT_SELECT
    )


def get_teacher_profile(user):
    return get_role_profile(
        user, models.Profile.ROLE_TEACHER, select_related=_TEACHER_SELECT
    )


def get_executive_profile(user):
    return get_role_profile(
        user, models.Profile.ROLE_EXECUTIVE, select_related=_EXECUTIVE_SELECT
    )
