from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

SESSION_EXP_CLAIM = "session_exp"


def issue_ums_refresh(user):
    refresh = RefreshToken.for_user(user)
    refresh[SESSION_EXP_CLAIM] = refresh["exp"]
    return refresh


def session_expiry_timestamp(refresh):
    session_exp = refresh.payload.get(SESSION_EXP_CLAIM)
    if session_exp is None:
        session_exp = refresh.payload.get("exp")
    try:
        return int(session_exp)
    except (TypeError, ValueError):
        raise AuthenticationFailed(
            "Invalid UMS session token.",
            "invalid_ums_session",
        )


def session_seconds_remaining(refresh):
    remaining = session_expiry_timestamp(refresh) - int(timezone.now().timestamp())
    if remaining <= 0:
        raise AuthenticationFailed(
            "Session expired. Please login again.",
            "ums_session_expired",
        )
    return remaining


def cap_token_to_ums_session(token, seconds_remaining):
    lifetime_seconds = min(
        int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        seconds_remaining,
    )
    token.set_exp(lifetime=timedelta(seconds=max(1, lifetime_seconds)))
    return token


def rotate_refresh_with_ums_session(refresh, seconds_remaining):
    absolute_session_expiry = session_expiry_timestamp(refresh)
    refresh.set_jti()
    refresh.set_iat()
    refresh[SESSION_EXP_CLAIM] = absolute_session_expiry
    refresh.set_exp(lifetime=timedelta(seconds=max(1, seconds_remaining)))
    return refresh
