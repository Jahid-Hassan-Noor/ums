import logging

from django.conf import settings
from django.core.mail import send_mail

from admin_app.settings_registry import setting_value
from auth_app.models import Profile
from notifications_package.models import Notification


logger = logging.getLogger(__name__)


def active_profiles_for_roles(*roles):
    return Profile.objects.filter(
        role__in=roles,
        is_active=True,
        user__is_active=True,
    )


def _notification_data(*, event_type, data=None, url=None):
    payload = dict(data or {})
    payload["event_type"] = event_type
    if url:
        payload["url"] = url
    return payload


def _absolute_ums_url(url):
    if not url:
        return ""
    if str(url).startswith(("http://", "https://")):
        return str(url)
    base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
    return f"{base_url}{url}" if base_url and str(url).startswith("/") else str(url)


def _profile_display_name(profile):
    user = profile.user
    return user.get_full_name().strip() or user.username


def _send_notification_email(*, recipient, subject, message, url=None):
    email = (recipient.user.email or "").strip()
    if not email:
        return False

    ums_url = _absolute_ums_url(url)
    body = [
        f"Hi {_profile_display_name(recipient)},",
        "",
        message,
    ]
    if ums_url:
        body.extend(["", f"Open in AIU Portal: {ums_url}"])

    try:
        send_mail(
            subject=subject,
            message="\n".join(body),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception(
            "Unable to send notification email to profile_id=%s.",
            recipient.pk,
        )
        return False


def notify_profiles(
    recipients,
    *,
    event_type,
    verb,
    actor=None,
    data=None,
    url=None,
    exclude_actor=False,
    email_subject=None,
    email_message=None,
):
    recipient_ids = {
        getattr(recipient, "pk", recipient)
        for recipient in recipients
        if getattr(recipient, "pk", recipient)
    }
    if exclude_actor and actor:
        recipient_ids.discard(actor.pk)
    if not recipient_ids:
        return []

    active_recipients = list(
        Profile.objects.select_related("user").filter(
            pk__in=recipient_ids,
            is_active=True,
            user__is_active=True,
        )
    )
    if not active_recipients:
        return []

    should_send_email = bool(email_subject) and setting_value(
        "notifications",
        "email_notifications_enabled",
    )
    email_body = email_message or verb
    if should_send_email:
        for recipient in active_recipients:
            _send_notification_email(
                recipient=recipient,
                subject=email_subject,
                message=email_body,
                url=url,
            )

    payload = _notification_data(event_type=event_type, data=data, url=url)
    return Notification.objects.bulk_create(
        [
            Notification(
                recipient=recipient,
                actor=actor,
                verb=verb,
                data=payload,
            )
            for recipient in active_recipients
        ],
        batch_size=500,
    )


def notify_profile(recipient, **kwargs):
    created = notify_profiles([recipient] if recipient else [], **kwargs)
    return created[0] if created else None


def notify_roles(roles, **kwargs):
    return notify_profiles(active_profiles_for_roles(*roles), **kwargs)
