from admin_app.settings_registry import setting_value
from auth_app.models import Profile
from notifications_package.service import notify_profile, notify_profiles
from technician_app import models


def eligible_students(election):
    students = Profile.objects.filter(
        role=Profile.ROLE_STUDENT,
        is_active=True,
        user__is_active=True,
    )
    if election.election_type == models.Election.TYPE_SCHOOL_COMMITTEE:
        students = students.filter(school=election.school)
    return students


def notify_election_students(election, *, event_type, verb):
    if not setting_value("notifications", "notify_elections"):
        return

    notify_profiles(
        eligible_students(election),
        actor=election.published_by or election.created_by,
        event_type=event_type,
        verb=verb,
        data={
            "election_id": election.id,
            "title": election.title,
            "status": election.status,
            "starts_at": election.starts_at.isoformat() if election.starts_at else None,
            "ends_at": election.ends_at.isoformat() if election.ends_at else None,
        },
        url="/student/elections",
    )


def notify_candidate(candidate, actor, verb):
    if not candidate.student_id or not setting_value("notifications", "notify_elections"):
        return

    notify_profile(
        candidate.student,
        actor=actor,
        event_type="elections.candidate_status_changed",
        verb=verb,
        data={
            "election_id": candidate.election_id,
            "candidate_id": candidate.id,
            "status": candidate.status,
        },
        url="/student/elections",
    )
