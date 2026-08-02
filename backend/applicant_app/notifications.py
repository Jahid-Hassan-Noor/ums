from auth_app.models import Profile
from admin_app.settings_registry import setting_value
from notifications_package.service import notify_profile, notify_roles


def notify_application_submitted(application):
    if not setting_value("notifications", "notify_applications"):
        return

    applicant = application.applicant.profile
    data = {
        "application_id": str(application.id),
        "application_number": application.application_number,
        "status": application.status,
    }
    notify_profile(
        applicant,
        actor=applicant,
        event_type="applications.submitted",
        verb=f"Application {application.application_number} submitted successfully.",
        data=data,
        url="/apply/status",
    )
    notify_roles(
        [Profile.ROLE_ADMIN],
        actor=applicant,
        event_type="applications.review_requested",
        verb=f"New admission application submitted: {application.application_number}",
        data=data,
        url="/admin/manage/applicants",
    )
    notify_roles(
        [Profile.ROLE_EXECUTIVE],
        actor=applicant,
        event_type="applications.review_requested",
        verb=f"New admission application submitted: {application.application_number}",
        data=data,
        url="/executive/dashboard",
    )


def notify_application_status_changed(application, reviewer):
    if not setting_value("notifications", "notify_applications"):
        return

    notify_profile(
        application.applicant.profile,
        actor=reviewer,
        event_type="applications.status_changed",
        verb=(
            f"Application {application.application_number} status changed to "
            f"{application.get_status_display()}."
        ),
        data={
            "application_id": str(application.id),
            "application_number": application.application_number,
            "status": application.status,
            "review_notes": application.review_notes,
        },
        url="/apply/status",
    )


def notify_scholarship_status_changed(scholarship):
    if not setting_value("notifications", "notify_applications"):
        return

    application = scholarship.application
    notify_profile(
        application.applicant.profile,
        actor=scholarship.reviewed_by,
        event_type="applications.scholarship_status_changed",
        verb=(
            f"Scholarship application for {application.application_number} changed to "
            f"{scholarship.get_status_display()}."
        ),
        data={
            "application_id": str(application.id),
            "application_number": application.application_number,
            "scholarship_status": scholarship.status,
        },
        url="/apply/status",
    )
