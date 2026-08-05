from django.urls import path
from rest_framework.permissions import AllowAny

from home_app.views import *


def public_view(view_class):
    return view_class.as_view(permission_classes=[AllowAny])


urlpatterns = [
    path("", public_view(PublicHome)),
    path("about", public_view(PublicAbout)),
    path("admissions", public_view(PublicAdmissions)),
    path("announcements", public_view(PublicAnnouncements)),
    path("centers", public_view(PublicCenters)),
    path("centers/<slug:slug>", public_view(PublicCenterDetail)),
    path("centres", public_view(PublicCentres)),
    path("centres/<slug:slug>", public_view(PublicCentreDetail)),
    path("contact", public_view(PublicContact)),
    path("departments", public_view(PublicDepartments)),
    path("directories", public_view(PublicDirectories)),
    path("events", public_view(PublicEvents)),
    path("events/<slug:slug>", public_view(PublicEventDetail)),
    path("login", public_view(PublicLogin)),
    path("news", public_view(PublicNews)),
    path("news/<slug:slug>", public_view(PublicNewsDetail)),
    path("notifications", PublicNotifications.as_view()),
    path("official-links", public_view(PublicOfficialLinks)),
    path("pages/navigation", public_view(PublicPageNavigation)),
    path("pages", public_view(PublicPageDetail)),
    path("pages/<path:route_path>", public_view(PublicPageDetail)),
    path("ums-overview", public_view(PublicUmsOverview)),
    path("profile", PublicProfile.as_view()),
    path("programmes", public_view(PublicProgrammes)),
    path("programs", public_view(PublicPrograms)),
    path("scholarship", public_view(PublicScholarship)),
    path("schools", public_view(PublicSchools)),
    path("schools/<slug:slug>", public_view(PublicSchoolDetail)),
    path("services", public_view(PublicServices)),
    path("settings/public", public_view(PublicSettings)),
    path("student-life", public_view(PublicStudentLife)),
    path("units", public_view(PublicUnits)),
]
