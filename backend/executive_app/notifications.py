from notifications_package.service import notify_profiles
from student_app.models import Enrollment


def _clock_value(value):
    return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value)[:5]


def notify_offering_teachers(offering, actor, *, event_type, verb):
    recipient_ids = {
        offering.instructor_id,
        *offering.class_meetings.values_list("lecturer_id", flat=True),
    }
    notify_profiles(
        [recipient_id for recipient_id in recipient_ids if recipient_id],
        actor=actor,
        event_type=event_type,
        verb=verb,
        data={
            "offering_id": offering.id,
            "course_code": offering.course.code,
            "course_title": offering.course.title,
            "semester": offering.semester.name,
            "section": offering.section,
        },
        url="/teacher/dashboard",
    )


def notify_meeting_change(meeting, actor, *, event_type, verb):
    notify_offering_teachers(
        meeting.offering,
        actor,
        event_type=event_type,
        verb=verb,
    )
    notify_profiles(
        Enrollment.objects.filter(
            offering=meeting.offering,
            completed_at__isnull=True,
        ).values_list("student_id", flat=True),
        actor=actor,
        event_type=event_type,
        verb=verb,
        data={
            "offering_id": meeting.offering_id,
            "class_meeting_id": meeting.id,
            "course_code": meeting.offering.course.code,
            "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
            "day_of_week": meeting.day_of_week,
            "start_time": _clock_value(meeting.start_time),
            "end_time": _clock_value(meeting.end_time),
        },
        url="/student/dashboard",
    )
