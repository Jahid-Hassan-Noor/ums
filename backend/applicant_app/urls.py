from django.urls import path

from applicant_app.views import *


urlpatterns = [
    path("options", ApplicantOptionsView.as_view()),
    path("auth/register", ApplicantRegisterView.as_view()),
    path("auth/login", ApplicantLoginView.as_view()),
    path("me", ApplicantMeView.as_view()),
    path("applications", ApplicationCollectionView.as_view()),
    path("applications/<uuid:application_id>", ApplicationDetailView.as_view()),
    path("applications/<uuid:application_id>/submit", ApplicationSubmitView.as_view()),
    path("applications/<uuid:application_id>/documents", ApplicationDocumentCollectionView.as_view()),
    path("staff/applications", StaffApplicationCollectionView.as_view()),
    path("staff/applications/<uuid:application_id>/status", StaffApplicationStatusView.as_view()),
    path("staff/applications/<uuid:application_id>/scholarship", StaffScholarshipReviewView.as_view()),
    path("staff/documents/<uuid:document_id>", StaffApplicationDocumentReviewView.as_view()),
]
