from django.urls import path

from notifications_package.views import (
    NotificationDeleteReadView,
    NotificationDeleteView,
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    summary,
)


urlpatterns = [
    path("", NotificationListView.as_view()),
    path("summary", summary.as_view()),
    path("summary/", summary.as_view()),
    path("read-all", NotificationReadAllView.as_view()),
    path("read-all/", NotificationReadAllView.as_view()),
    path("read", NotificationDeleteReadView.as_view()),
    path("read/", NotificationDeleteReadView.as_view()),
    path("<int:notification_id>/read", NotificationReadView.as_view()),
    path("<int:notification_id>/read/", NotificationReadView.as_view()),
    path("<int:notification_id>", NotificationDeleteView.as_view()),
    path("<int:notification_id>/", NotificationDeleteView.as_view()),
]
