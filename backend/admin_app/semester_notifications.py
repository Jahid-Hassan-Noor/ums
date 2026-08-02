from admin_app import models
from notifications_package.service import notify_roles
from student_app.models import RegistrationPeriod


def notify_semester_event(semester, actor, *, event_type, verb):
    periods = [
        {
            "title": period.title,
            "phase": period.phase,
            "opens_at": period.opens_at.isoformat(),
            "closes_at": period.closes_at.isoformat(),
        }
        for period in RegistrationPeriod.objects.filter(semester=semester).order_by("opens_at")
    ]
    data = {
        "semester_id": semester.id,
        "semester": semester.name,
        "academic_session": semester.academic_session,
        "start_date": semester.start_date.isoformat(),
        "end_date": semester.end_date.isoformat(),
        "registration_periods": periods,
    }
    notify_roles(
        [models.Profile.ROLE_STUDENT],
        actor=actor,
        event_type=event_type,
        verb=verb,
        data=data,
        url="/student/registration",
    )
    notify_roles(
        [models.Profile.ROLE_TEACHER],
        actor=actor,
        event_type=event_type,
        verb=verb,
        data=data,
        url="/teacher/dashboard",
    )
    notify_roles(
        [models.Profile.ROLE_EXECUTIVE],
        actor=actor,
        event_type=event_type,
        verb=verb,
        data=data,
        url="/executive/manage/schedule",
    )
