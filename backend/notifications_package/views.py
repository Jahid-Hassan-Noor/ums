from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import Profile
from auth_app.permissions import IsActiveUmsUser
from notifications_package.models import Notification


def profile_for_user(user):
    return Profile.objects.filter(user=user).first()


def actor_name(actor):
    if not actor:
        return None
    full_name = actor.user.get_full_name().strip()
    return full_name or actor.user.username


def serialize_notification(notification):
    actor = notification.actor
    return {
        "id": notification.id,
        "verb": notification.verb,
        "unread": notification.unread,
        "data": notification.data or {},
        "created_at": notification.created_at.isoformat(),
        "actor": (
            {
                "name": actor_name(actor),
                "role": actor.role,
            }
            if actor
            else None
        ),
    }


class NotificationListView(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request):
        profile = profile_for_user(request.user)
        if not profile:
            return Response(
                {"notifications": [], "unread_count": 0, "total_count": 0},
                status=status.HTTP_200_OK,
            )

        notifications = Notification.objects.filter(recipient=profile).select_related(
            "actor__user"
        )
        total_count = notifications.count()
        unread_count = notifications.filter(unread=True).count()
        notifications = notifications.order_by("-created_at", "-id")[:100]

        return Response(
            {
                "notifications": [
                    serialize_notification(notification)
                    for notification in notifications
                ],
                "unread_count": unread_count,
                "total_count": total_count,
            },
            status=status.HTTP_200_OK,
        )


class NotificationSummaryView(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request, *args, **kwargs):
        profile = Profile.objects.filter(user=request.user).first()
        unread_count = 0
        if profile:
            unread_count = Notification.objects.filter(
                recipient=profile,
                unread=True,
            ).count()

        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class NotificationReadView(APIView):
    permission_classes = [IsActiveUmsUser]

    def post(self, request, notification_id):
        profile = profile_for_user(request.user)
        notification = (
            Notification.objects.filter(id=notification_id, recipient=profile).first()
            if profile
            else None
        )
        if not notification:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if notification.unread:
            notification.unread = False
            notification.save(update_fields=["unread"])

        return Response(
            {
                "notification": serialize_notification(notification),
                "unread_count": Notification.objects.filter(
                    recipient=profile,
                    unread=True,
                ).count(),
            },
            status=status.HTTP_200_OK,
        )


class NotificationReadAllView(APIView):
    permission_classes = [IsActiveUmsUser]

    def post(self, request):
        profile = profile_for_user(request.user)
        updated_count = 0
        if profile:
            updated_count = Notification.objects.filter(
                recipient=profile,
                unread=True,
            ).update(unread=False)

        return Response(
            {"updated_count": updated_count, "unread_count": 0},
            status=status.HTTP_200_OK,
        )


class NotificationDeleteView(APIView):
    permission_classes = [IsActiveUmsUser]

    def delete(self, request, notification_id):
        profile = profile_for_user(request.user)
        notification = (
            Notification.objects.filter(id=notification_id, recipient=profile).first()
            if profile
            else None
        )
        if not notification:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.delete()
        unread_count = (
            Notification.objects.filter(recipient=profile, unread=True).count()
            if profile
            else 0
        )
        total_count = (
            Notification.objects.filter(recipient=profile).count() if profile else 0
        )

        return Response(
            {
                "deleted_count": 1,
                "unread_count": unread_count,
                "total_count": total_count,
            },
            status=status.HTTP_200_OK,
        )


class NotificationDeleteReadView(APIView):
    permission_classes = [IsActiveUmsUser]

    def delete(self, request):
        profile = profile_for_user(request.user)
        deleted_count = 0
        if profile:
            read_notifications = Notification.objects.filter(
                recipient=profile,
                unread=False,
            )
            deleted_count = read_notifications.count()
            read_notifications.delete()

        unread_count = (
            Notification.objects.filter(recipient=profile, unread=True).count()
            if profile
            else 0
        )
        total_count = (
            Notification.objects.filter(recipient=profile).count() if profile else 0
        )

        return Response(
            {
                "deleted_count": deleted_count,
                "unread_count": unread_count,
                "total_count": total_count,
            },
            status=status.HTTP_200_OK,
        )


summary = NotificationSummaryView
