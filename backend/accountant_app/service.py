import json
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from textwrap import wrap
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from accountant_app.models import FinanceGatewayConfig, PaymentAttempt, Subscription, SubscriptionPlan
from admin_app.models import Profile
from admin_app.settings_registry import (
    default_currency_code,
    format_currency_amount,
    institution_identity,
    payment_reference_prefix,
)
from core.common.money import format_money as money
from core.common.profiles import (
    profile_display_name as display_name,
    profile_identifier,
)
from notifications_package.service import notify_profile


logger = logging.getLogger(__name__)

SUBSCRIPTION_ROLE_OPTIONS = [
    (role, label)
    for role, label in Profile.ROLE_CHOICES
    if role != Profile.ROLE_APPLICANT
]
SUBSCRIPTION_ROLE_VALUES = [role for role, _label in SUBSCRIPTION_ROLE_OPTIONS]


def _money_label(amount, currency):
    return format_currency_amount(amount, currency_code=currency)


def _provider_options_payload():
    return [
        {"value": value, "label": label}
        for value, label in FinanceGatewayConfig.PROVIDER_CHOICES
    ]


def _is_manual_gateway(config):
    return not config.is_active or config.provider == FinanceGatewayConfig.PROVIDER_MANUAL


def subscription_role_options_payload():
    return [{"value": role, "label": label} for role, label in SUBSCRIPTION_ROLE_OPTIONS]


def normalized_plan_roles(value):
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValidationError({"available_roles": "Subscription roles must be a list."})
    incoming = {str(role).strip().lower() for role in value if str(role).strip()}
    unknown = sorted(incoming - set(SUBSCRIPTION_ROLE_VALUES))
    if unknown:
        raise ValidationError({"available_roles": f"Unknown subscription roles: {', '.join(unknown)}."})
    return [role for role in SUBSCRIPTION_ROLE_VALUES if role in incoming]


def allowed_roles_for_plan(plan):
    if plan.available_to_all_roles:
        return list(SUBSCRIPTION_ROLE_VALUES)
    return normalized_plan_roles(plan.available_roles)

def role_can_buy(profile, plan):
    return profile.role in allowed_roles_for_plan(plan)


def plan_payload(plan, profile=None):
    payload = {
        "id": plan.id,
        "subscription_type": plan.subscription_type,
        "name": plan.name,
        "description": plan.description,
        "price": money(plan.price),
        "price_display": format_currency_amount(plan.price),
        "currency": default_currency_code(),
        "duration_days": plan.duration_days,
        "is_active": plan.is_active,
        "available_to_all_roles": plan.available_to_all_roles,
        "available_roles": list(plan.available_roles or []),
        "allowed_roles": allowed_roles_for_plan(plan),
    }
    if profile:
        payload["can_purchase"] = plan.is_active and role_can_buy(profile, plan)
    return payload


def subscription_payload(subscription):
    plan = subscription.plan
    return {
        "id": subscription.id,
        "plan": plan_payload(plan),
        "subscriber": {
            "id": subscription.subscriber_id,
            "name": display_name(subscription.subscriber),
            "role": subscription.subscriber.role,
            "identifier": profile_identifier(subscription.subscriber),
            "email": subscription.subscriber.user.email,
        },
        "status": subscription.status,
        "amount": money(subscription.amount),
        "amount_display": _money_label(subscription.amount, subscription.currency),
        "currency": subscription.currency,
        "starts_at": subscription.starts_at.isoformat() if subscription.starts_at else None,
        "ends_at": subscription.ends_at.isoformat() if subscription.ends_at else None,
        "is_current": subscription.is_current,
        "gateway_bill_code": subscription.gateway_bill_code,
        "checkout_url": subscription.checkout_url,
        "card_url": f"/finance/subscriptions/{subscription.id}/card",
        "created_at": subscription.created_at.isoformat(),
        "updated_at": subscription.updated_at.isoformat(),
    }


def gateway_config_payload(config):
    return {
        "provider": config.provider,
        "provider_label": config.provider_label,
        "provider_options": _provider_options_payload(),
        "mode": config.mode,
        "merchant_name": config.merchant_name,
        "api_base_url": config.api_base_url,
        "checkout_base_url": config.checkout_base_url,
        "category_code": config.category_code,
        "secret_key_present": bool(config.secret_key),
        "secret_key_preview": config.secret_key_preview,
        "callback_token_present": bool(config.callback_token),
        "callback_token_preview": config.callback_token_preview,
        "is_active": config.is_active,
        "requires_checkout_configuration": config.uses_external_checkout,
        "is_manual": _is_manual_gateway(config),
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


def configured_gateway():
    config = FinanceGatewayConfig.objects.filter(pk=1, is_active=True).first()
    if not config:
        raise ValidationError("Finance payment gateway is not active. Please contact to the finance department.")
    if config.provider == FinanceGatewayConfig.PROVIDER_MANUAL:
        raise ValidationError("Manual/offline payment mode is active.")
    config.full_clean()
    return config


def save_gateway_config(*, actor, data):
    config, _created = FinanceGatewayConfig.objects.get_or_create(pk=1)
    simple_fields = (
        "provider",
        "mode",
        "merchant_name",
        "api_base_url",
        "checkout_base_url",
        "category_code",
        "is_active",
    )
    for field in simple_fields:
        if field in data:
            setattr(config, field, data.get(field))
    if data.get("secret_key"):
        config.secret_key = str(data.get("secret_key")).strip()
    if data.get("clear_secret_key"):
        config.secret_key = ""
    if data.get("callback_token"):
        config.callback_token = str(data.get("callback_token")).strip()
    if data.get("clear_callback_token"):
        config.callback_token = ""
    config.updated_by = actor
    config.save()
    return config


def boolean_value(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def positive_int(value, *, field_name, default=None):
    if value in (None, ""):
        if default is not None:
            return default
        raise ValidationError({field_name: "This field is required."})
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValidationError({field_name: "Enter a valid whole number."}) from error
    if parsed < 1:
        raise ValidationError({field_name: "Enter a value of at least 1."})
    return parsed


def decimal_value(value, *, field_name):
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValidationError({field_name: "Enter a valid amount."}) from error


def subscription_code(value, fallback_name):
    code = slugify(str(value or fallback_name or "").strip()).lower()
    if not code:
        raise ValidationError({"subscription_type": "Subscription code is required."})
    return code[:50]


def apply_plan_data(plan, *, actor, data, creating=False):
    if creating and not str(data.get("name") or "").strip():
        raise ValidationError({"name": "Subscription name is required."})
    if "name" in data or creating:
        plan.name = str(data.get("name") or "").strip()
    if "subscription_type" in data or creating:
        plan.subscription_type = subscription_code(data.get("subscription_type"), plan.name)
    if "description" in data or creating:
        plan.description = str(data.get("description") or "").strip()
    if "price" in data or creating:
        plan.price = decimal_value(data.get("price"), field_name="price")
    if "duration_days" in data or creating:
        plan.duration_days = positive_int(data.get("duration_days"), field_name="duration_days", default=30)
    if "is_active" in data or creating:
        plan.is_active = boolean_value(data.get("is_active"), True)
    if "available_to_all_roles" in data or creating:
        plan.available_to_all_roles = boolean_value(data.get("available_to_all_roles"), True)
    if "available_roles" in data:
        plan.available_roles = normalized_plan_roles(data.get("available_roles"))
        if plan.available_roles and "available_to_all_roles" not in data:
            plan.available_to_all_roles = False
    plan.updated_by = actor
    plan.save()
    return plan


def create_plan(*, actor, data):
    plan = SubscriptionPlan()
    return apply_plan_data(plan, actor=actor, data=data, creating=True)


def update_plan(*, actor, plan_id, data):
    plan = SubscriptionPlan.objects.get(pk=plan_id)
    return apply_plan_data(plan, actor=actor, data=data)


def delete_plan(*, actor, plan_id):
    plan = SubscriptionPlan.objects.get(pk=plan_id)
    if plan.subscriptions.exists():
        plan.is_active = False
        plan.updated_by = actor
        plan.save(update_fields=["is_active", "updated_by", "updated_at"])
        return plan, False
    try:
        plan.delete()
    except ProtectedError:
        plan.is_active = False
        plan.updated_by = actor
        plan.save(update_fields=["is_active", "updated_by", "updated_at"])
        return plan, False
    return None, True


def my_subscriptions_payload(profile):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by("subscription_type")
    subscriptions = (
        Subscription.objects.select_related("plan", "subscriber", "subscriber__user")
        .filter(subscriber=profile)
        .order_by("-created_at")[:20]
    )
    return {
        "plans": [
            plan_payload(plan, profile)
            for plan in plans
            if role_can_buy(profile, plan)
        ],
        "subscriptions": [subscription_payload(subscription) for subscription in subscriptions],
    }


def accountant_dashboard_payload():
    now = timezone.now()
    subscriptions = Subscription.objects.select_related("plan", "subscriber", "subscriber__user")
    from accountant_app.models import StudentBalanceSnapshot, StudentFinanceHold, StudentLedgerEntry

    outstanding = StudentBalanceSnapshot.objects.filter(balance__gt=0)
    return {
        "summary": {
            "active": subscriptions.filter(status=Subscription.STATUS_ACTIVE, ends_at__gte=now).count(),
            "pending": subscriptions.filter(status=Subscription.STATUS_PENDING).count(),
            "expired": subscriptions.filter(status=Subscription.STATUS_ACTIVE, ends_at__lt=now).count(),
            "successful_payments": PaymentAttempt.objects.filter(status=PaymentAttempt.STATUS_SUCCEEDED).count(),
            "outstanding_balance": money(sum((item.balance for item in outstanding), Decimal("0.00"))),
            "students_with_balance": outstanding.count(),
            "active_finance_holds": StudentFinanceHold.objects.filter(is_active=True).count(),
            "ledger_entries": StudentLedgerEntry.objects.count(),
        },
        "gateway": gateway_config_payload(FinanceGatewayConfig.objects.get_or_create(pk=1)[0]),
        "plans": [plan_payload(plan) for plan in SubscriptionPlan.objects.order_by("subscription_type")],
        "role_options": subscription_role_options_payload(),
        "recent_subscriptions": [
            subscription_payload(subscription)
            for subscription in subscriptions.order_by("-created_at")[:25]
        ],
    }


def _absolute_frontend_url(path):
    base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
    return f"{base_url}{path}" if base_url else path


def _absolute_backend_url(request, route_name):
    path = reverse(route_name)
    base_url = getattr(settings, "PUBLIC_BACKEND_BASE_URL", "").rstrip("/")
    if base_url:
        return f"{base_url}{path}"
    return request.build_absolute_uri(path)


def _callback_url(request, config):
    url = _absolute_backend_url(request, "finance_payment_webhook")
    if config.callback_token:
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}token={config.callback_token}"
    return url


def _gateway_payload(*, request, config, subscription, attempt):
    profile = subscription.subscriber
    plan = subscription.plan
    amount_in_cents = int(subscription.amount * 100)
    return {
        "userSecretKey": config.secret_key,
        "categoryCode": config.category_code,
        "billName": f"{plan.name} ({plan.duration_days} Days)",
        "billDescription": f"{plan.name} subscription for {display_name(profile)}",
        "billPriceSetting": 1,
        "billPayorInfo": 1,
        "billAmount": amount_in_cents,
        "billReturnUrl": _absolute_backend_url(request, "finance_payment_return"),
        "billCallbackUrl": _callback_url(request, config),
        "billExternalReferenceNo": attempt.external_reference,
        "billTo": display_name(profile),
        "billEmail": profile.user.email,
        "billPhone": profile.phone or "0000000000",
        "merchantName": config.merchant_name,
    }


def _parse_gateway_response(raw_text):
    parsed = json.loads(raw_text)
    if isinstance(parsed, list) and parsed:
        item = parsed[0]
    elif isinstance(parsed, dict):
        item = parsed
    else:
        raise ValidationError("Payment gateway returned an empty response.")
    return parsed, item


def _post_form(url, payload):
    encoded = urlencode(payload).encode("utf-8")
    request = Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8")
    except URLError as error:
        raise ValidationError(f"Payment gateway request failed: {error}") from error


def _create_gateway_checkout(config, payload):
    parsed, item = _parse_gateway_response(_post_form(config.api_base_url, payload))
    bill_code = (
        item.get("BillCode")
        or item.get("billCode")
        or item.get("bill_code")
        or item.get("billcode")
        or item.get("id")
        or ""
    )
    checkout_url = (
        item.get("checkout_url")
        or item.get("payment_url")
        or item.get("url")
        or ""
    )
    if not checkout_url and bill_code:
        checkout_url = f"{config.checkout_base_url.rstrip('/')}/{bill_code}"
    if not checkout_url:
        raise ValidationError("Payment gateway did not return a checkout URL or bill code.")
    return {
        "raw": parsed,
        "gateway_reference": str(bill_code),
        "checkout_url": str(checkout_url),
    }


@transaction.atomic
def initiate_subscription_payment(*, profile, plan_id, request):
    plan = SubscriptionPlan.objects.select_for_update().filter(pk=plan_id, is_active=True).first()
    if not plan:
        raise ValidationError("Subscription plan not found or inactive.")
    if not role_can_buy(profile, plan):
        raise ValidationError("Your role is not eligible for this subscription.")
    if plan.price <= 0:
        raise ValidationError("This subscription price is not configured yet.")

    config = FinanceGatewayConfig.objects.get_or_create(pk=1)[0]
    currency = default_currency_code()
    subscription = Subscription.objects.create(
        subscriber=profile,
        plan=plan,
        amount=plan.price,
        currency=currency,
    )
    attempt = PaymentAttempt.objects.create(
        subscription=subscription,
        payer=profile,
        amount=plan.price,
        currency=currency,
        external_reference=f"{payment_reference_prefix()}-SUB-{subscription.id}-{uuid4().hex[:12]}",
    )
    subscription.external_reference = attempt.external_reference
    subscription.save(update_fields=["external_reference", "updated_at"])

    if _is_manual_gateway(config):
        attempt.gateway_reference = attempt.external_reference
        attempt.request_payload = {
            "provider": config.provider,
            "mode": "manual",
            "message": "Manual/offline payment request recorded.",
        }
        attempt.save(update_fields=["request_payload", "gateway_reference", "updated_at"])
        subscription.gateway_bill_code = attempt.gateway_reference
        subscription.save(update_fields=["gateway_bill_code", "updated_at"])
        return subscription, attempt

    config.full_clean()

    payload = _gateway_payload(
        request=request,
        config=config,
        subscription=subscription,
        attempt=attempt,
    )
    attempt.request_payload = {key: ("***" if key == "userSecretKey" else value) for key, value in payload.items()}
    gateway_response = _create_gateway_checkout(config, payload)
    attempt.gateway_reference = gateway_response["gateway_reference"]
    attempt.checkout_url = gateway_response["checkout_url"]
    attempt.response_payload = gateway_response["raw"]
    attempt.save(update_fields=["request_payload", "gateway_reference", "checkout_url", "response_payload", "updated_at"])

    subscription.gateway_bill_code = attempt.gateway_reference
    subscription.checkout_url = attempt.checkout_url
    subscription.save(update_fields=["gateway_bill_code", "checkout_url", "updated_at"])
    return subscription, attempt


def _current_active_subscription(profile, plan):
    return (
        Subscription.objects.filter(
            subscriber=profile,
            plan=plan,
            status=Subscription.STATUS_ACTIVE,
            ends_at__gte=timezone.now(),
        )
        .order_by("-ends_at")
        .first()
    )


def build_subscription_card_pdf(subscription):
    from reportlab.lib.pagesizes import landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as reportlab_canvas

    page_size = landscape((86 * mm, 54 * mm))
    buffer = BytesIO()
    pdf = reportlab_canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size
    profile = subscription.subscriber
    plan = subscription.plan
    identity = institution_identity()
    institution_name = (
        identity.get("legal_name")
        or identity.get("university_name")
        or "University"
    ).upper()
    short_name = identity.get("short_name") or "Portal"

    pdf.setLineWidth(1)
    pdf.roundRect(8, 8, width - 16, height - 16, 8, stroke=1, fill=0)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(18, height - 26, institution_name[:46])
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(18, height - 47, f"{plan.name.upper()} CARD")
    pdf.setFont("Helvetica", 8)
    rows = [
        ("Name", display_name(profile)),
        ("ID", profile_identifier(profile)),
        ("Role", profile.role.title()),
        ("Valid From", timezone.localtime(subscription.starts_at).strftime("%d %b %Y") if subscription.starts_at else ""),
        ("Valid Until", timezone.localtime(subscription.ends_at).strftime("%d %b %Y") if subscription.ends_at else ""),
        ("Ref", subscription.external_reference or str(subscription.id)),
    ]
    y = height - 66
    for label, value in rows:
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.drawString(18, y, f"{label}:")
        pdf.setFont("Helvetica", 7.5)
        text = str(value or "")
        for index, line in enumerate(wrap(text, width=34)[:2] or [""]):
            pdf.drawString(70, y - (index * 8), line)
        y -= 13
    pdf.setFont("Helvetica-Oblique", 6.5)
    pdf.drawRightString(width - 18, 18, f"Generated by {short_name} Portal Finance")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def subscription_card_response(subscription):
    filename = f"{subscription.plan.subscription_type}-subscription-card-{subscription.id}.pdf"
    response = HttpResponse(build_subscription_card_pdf(subscription), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def send_subscription_receipt(subscription):
    profile = subscription.subscriber
    email = (profile.user.email or "").strip()
    card_path = _absolute_frontend_url(f"{subscription_card_public_path(subscription)}")
    message = "\n".join(
        [
            f"Hello {display_name(profile)},",
            "",
            f"Your {subscription.plan.name} payment was successful.",
            f"Amount: {_money_label(subscription.amount, subscription.currency)}",
            f"Valid from: {timezone.localtime(subscription.starts_at).strftime('%d %B %Y')}",
            f"Valid until: {timezone.localtime(subscription.ends_at).strftime('%d %B %Y')}",
            f"Reference: {subscription.external_reference}",
            "",
            f"Printable card: {card_path}",
            "",
            "A PDF copy of the card is attached.",
        ]
    )
    if email:
        try:
            identity = institution_identity()
            subject_prefix = (
                identity.get("short_name")
                or identity.get("university_name")
                or "University"
            )
            email_message = EmailMessage(
                subject=f"{subject_prefix} {subscription.plan.name} subscription card",
                body=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[email],
            )
            email_message.attach(
                f"{subscription.plan.subscription_type}-subscription-card.pdf",
                build_subscription_card_pdf(subscription),
                "application/pdf",
            )
            email_message.send(fail_silently=False)
        except Exception:
            logger.exception("Unable to send subscription receipt for subscription_id=%s.", subscription.id)
    notify_profile(
        profile,
        event_type="finance.subscription_activated",
        verb=f"Your {subscription.plan.name} subscription is active until {timezone.localtime(subscription.ends_at).strftime('%d %b %Y')}.",
        data={
            "subscription_id": subscription.id,
            "plan": subscription.plan.subscription_type,
            "ends_at": subscription.ends_at.isoformat() if subscription.ends_at else None,
        },
        url=subscription_card_public_path(subscription),
    )


def subscription_card_public_path(subscription):
    role = subscription.subscriber.role
    base = {
        Profile.ROLE_STUDENT: "/student/subscriptions",
        Profile.ROLE_TEACHER: "/teacher/subscriptions",
        Profile.ROLE_ADMIN: "/admin/subscriptions",
        Profile.ROLE_EXECUTIVE: "/executive/subscriptions",
        Profile.ROLE_LIBRARIAN: "/librarian/subscriptions",
        Profile.ROLE_CATERER: "/caterer/subscriptions",
        Profile.ROLE_TECHNICIAN: "/technician/subscriptions",
        Profile.ROLE_ACCOUNTANT: "/accountant/my-subscriptions",
        Profile.ROLE_HR: "/hr/subscriptions",
    }.get(role, "/profile")
    return base


@transaction.atomic
def activate_payment_attempt(attempt, callback_payload=None):
    attempt = PaymentAttempt.objects.select_for_update().select_related(
        "subscription",
        "subscription__plan",
        "subscription__subscriber",
        "subscription__subscriber__user",
    ).get(pk=attempt.pk)
    subscription = attempt.subscription
    if attempt.status == PaymentAttempt.STATUS_SUCCEEDED and subscription.status == Subscription.STATUS_ACTIVE:
        return subscription

    now = timezone.now()
    current = _current_active_subscription(subscription.subscriber, subscription.plan)
    starts_at = current.ends_at if current and current.ends_at and current.ends_at > now else now
    ends_at = starts_at + timedelta(days=subscription.plan.duration_days)
    attempt.status = PaymentAttempt.STATUS_SUCCEEDED
    attempt.paid_at = now
    if callback_payload is not None:
        attempt.callback_payload = callback_payload
    attempt.save(update_fields=["status", "paid_at", "callback_payload", "updated_at"])

    subscription.status = Subscription.STATUS_ACTIVE
    subscription.starts_at = starts_at
    subscription.ends_at = ends_at
    subscription.activated_at = now
    subscription.gateway_bill_code = attempt.gateway_reference
    subscription.checkout_url = attempt.checkout_url
    subscription.save(update_fields=[
        "status",
        "starts_at",
        "ends_at",
        "activated_at",
        "gateway_bill_code",
        "checkout_url",
        "updated_at",
    ])
    transaction.on_commit(lambda: send_subscription_receipt(subscription))
    return subscription


def mark_payment_attempt(attempt, status, callback_payload=None):
    attempt.status = status
    if callback_payload is not None:
        attempt.callback_payload = callback_payload
    attempt.save(update_fields=["status", "callback_payload", "updated_at"])
    subscription = attempt.subscription
    if status == PaymentAttempt.STATUS_FAILED:
        subscription.status = Subscription.STATUS_FAILED
    elif status == PaymentAttempt.STATUS_CANCELLED:
        subscription.status = Subscription.STATUS_CANCELLED
    else:
        return subscription
    subscription.save(update_fields=["status", "updated_at"])
    return subscription


def find_payment_attempt(payload):
    external_reference = (
        payload.get("order_id")
        or payload.get("external_reference")
        or payload.get("billExternalReferenceNo")
        or payload.get("reference")
    )
    bill_code = (
        payload.get("billcode")
        or payload.get("bill_code")
        or payload.get("BillCode")
        or payload.get("billCode")
    )
    attempts = PaymentAttempt.objects.select_related("subscription", "subscription__plan", "subscription__subscriber", "subscription__subscriber__user")
    if external_reference:
        attempt = attempts.filter(external_reference=external_reference).first()
        if attempt:
            return attempt
    if bill_code:
        return attempts.filter(gateway_reference=bill_code).first()
    return None


def process_gateway_callback(payload):
    external_reference = (
        payload.get("order_id")
        or payload.get("external_reference")
        or payload.get("billExternalReferenceNo")
        or payload.get("reference")
    )
    bill_code = (
        payload.get("billcode")
        or payload.get("bill_code")
        or payload.get("BillCode")
        or payload.get("billCode")
    )

    from accountant_app.models import Fine
    fine = None
    if external_reference and str(external_reference).startswith("FINE-"):
        try:
            fine_id = int(str(external_reference).split("-")[1])
            fine = Fine.objects.filter(pk=fine_id).first()
        except (ValueError, IndexError):
            pass
    if not fine and bill_code:
        fine = Fine.objects.filter(gateway_bill_code=bill_code).first()

    if fine:
        status_value = str(payload.get("status") or payload.get("status_id") or payload.get("payment_status") or "").strip().lower()
        if status_value in {"1", "success", "successful", "succeeded", "paid", "completed"}:
            from accountant_app.fine_service import mark_fine_paid
            mark_fine_paid(fine)
        return None

    attempt = find_payment_attempt(payload)
    if not attempt:
        logger.warning("Finance payment callback did not match an attempt: %s", payload)
        return None
    status_value = str(payload.get("status") or payload.get("status_id") or payload.get("payment_status") or "").strip().lower()
    if status_value in {"1", "success", "successful", "succeeded", "paid", "completed"}:
        return activate_payment_attempt(attempt, callback_payload=payload)
    if status_value in {"3", "cancelled", "canceled", "cancel"}:
        return mark_payment_attempt(attempt, PaymentAttempt.STATUS_CANCELLED, callback_payload=payload)
    return mark_payment_attempt(attempt, PaymentAttempt.STATUS_FAILED, callback_payload=payload)
