from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accountant_app.models import FinanceGatewayConfig, Subscription, SubscriptionPlan
from accountant_app.service import (
    accountant_dashboard_payload,
    create_plan,
    delete_plan,
    gateway_config_payload,
    initiate_subscription_payment,
    my_subscriptions_payload,
    plan_payload,
    process_gateway_callback,
    save_gateway_config,
    subscription_role_options_payload,
    subscription_card_response,
    subscription_payload,
    update_plan,
)
from admin_app.models import Profile
from auth_app.permissions import IsAccountantRole, IsActiveUmsUser


def validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(error, "messages"):
        return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class AccountantUms(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        return Response({"title": "Accountant Portal", "section": "accountant"})


class AccountantDashboard(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        return Response({"title": "Finance Dashboard", "section": "accountant", **accountant_dashboard_payload()})


class FinanceGatewaySettings(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        config = FinanceGatewayConfig.objects.get_or_create(pk=1)[0]
        return Response({"gateway": gateway_config_payload(config)})

    def patch(self, request):
        try:
            config = save_gateway_config(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return validation_response(error)
        return Response({"message": "Payment gateway settings updated.", "gateway": gateway_config_payload(config)})


class FinancePlans(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        plans = SubscriptionPlan.objects.order_by("subscription_type")
        return Response({"plans": [plan_payload(plan) for plan in plans], "role_options": subscription_role_options_payload()})

    def post(self, request):
        try:
            plan = create_plan(actor=request.user.profile, data=request.data)
        except (ValidationError, ValueError) as error:
            return validation_response(error)
        return Response({"message": "Subscription option created.", "plan": plan_payload(plan)}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        try:
            plan = update_plan(
                actor=request.user.profile,
                plan_id=request.data.get("plan_id"),
                data=request.data,
            )
        except SubscriptionPlan.DoesNotExist:
            return Response({"detail": "Subscription plan not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError) as error:
            return validation_response(error)
        return Response({"message": "Subscription plan updated.", "plan": plan_payload(plan)})

    def delete(self, request):
        try:
            plan, deleted = delete_plan(
                actor=request.user.profile,
                plan_id=request.data.get("plan_id") or request.query_params.get("plan_id"),
            )
        except SubscriptionPlan.DoesNotExist:
            return Response({"detail": "Subscription plan not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError) as error:
            return validation_response(error)
        if deleted:
            return Response({"message": "Subscription option deleted.", "deleted": True})
        return Response({
            "message": "Subscription option has payment history, so it was deactivated.",
            "deleted": False,
            "plan": plan_payload(plan),
        })


class MySubscriptions(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request):
        return Response(my_subscriptions_payload(request.user.profile))


class SubscriptionPurchase(APIView):
    permission_classes = [IsActiveUmsUser]

    def post(self, request):
        try:
            subscription, attempt = initiate_subscription_payment(
                profile=request.user.profile,
                plan_id=request.data.get("plan_id"),
                request=request,
            )
        except ValidationError as error:
            return validation_response(error)
        return Response(
            {
                "message": "Payment checkout created.",
                "subscription": subscription_payload(subscription),
                "checkout_url": attempt.checkout_url,
            },
            status=status.HTTP_201_CREATED,
        )


class AccountantSubscriptions(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        subscriptions = Subscription.objects.select_related("plan", "subscriber", "subscriber__user").order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            subscriptions = subscriptions.filter(status=status_filter)
        return Response({"subscriptions": [subscription_payload(item) for item in subscriptions[:100]]})


class SubscriptionCard(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request, pk):
        subscription = (
            Subscription.objects.select_related("plan", "subscriber", "subscriber__user")
            .filter(pk=pk)
            .first()
        )
        if not subscription:
            return Response({"detail": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        profile = request.user.profile
        if subscription.subscriber_id != profile.id and profile.role not in {Profile.ROLE_ACCOUNTANT, Profile.ROLE_ADMIN}:
            return Response({"detail": "You cannot access this subscription card."}, status=status.HTTP_403_FORBIDDEN)
        if subscription.status != Subscription.STATUS_ACTIVE:
            return Response({"detail": "A printable card is only available after payment activation."}, status=status.HTTP_400_BAD_REQUEST)
        return subscription_card_response(subscription)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhook(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def post(self, request):
        config = FinanceGatewayConfig.objects.filter(pk=1, is_active=True).first()
        callback_token = config.callback_token if config else ""
        supplied_token = request.query_params.get("token") or request.headers.get("X-AIU-Gateway-Token", "")
        if callback_token and not constant_time_compare(str(supplied_token), callback_token):
            return Response({"detail": "Invalid callback token."}, status=status.HTTP_403_FORBIDDEN)
        payload = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        process_gateway_callback(payload)
        return Response({"ok": True})


class PaymentReturn(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        status_value = str(request.query_params.get("status_id") or request.query_params.get("status") or "").lower()
        if status_value in {"1", "success", "successful", "paid", "completed"}:
            outcome = "success"
        elif status_value in {"3", "failed", "cancelled", "canceled", "cancel"}:
            outcome = "failed"
        else:
            outcome = "pending"
        frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
        if frontend_base_url:
            return redirect(f"{frontend_base_url}/payment-return?status={outcome}")
        return Response({"status": outcome})
