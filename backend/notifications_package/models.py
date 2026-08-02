from django.db import models

from auth_app.models import Profile


class Notification(models.Model):
    recipient = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acted_notifications",
    )
    verb = models.CharField(max_length=255)
    unread = models.BooleanField(default=True)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_app_notification"

    def __str__(self):
        return f"Notification to {self.recipient_id}: {self.verb}"
