import re
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from admin_app.models import ClassMeeting, CourseOffering, Profile
from home_app import models as public_models
from home_app.views.public_helpers import (
    get_public_page,
    public_announcements,
    public_official_links,
    published_events,
    published_news,
)
from student_app.models import Enrollment
from student_app.registration_service import get_student_profile, selected_class_meetings
from teacher_app.assignment_service import (
    get_teacher_profile,
    student_assignments,
    teacher_offerings,
)
from teacher_app.calendar_service import student_calendar_payload, teacher_calendar_payload
from teacher_app.models import Assignment


ACTIVE_CLASS_STATUSES = {
    ClassMeeting.STATUS_IMPORTED,
    ClassMeeting.STATUS_SCHEDULED,
}


def display_name(profile):
    if not profile:
        return ""
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def profile_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return (
        Profile.objects.select_related("user")
        .filter(user=user, is_active=True)
        .first()
    )


def current_role(user):
    profile = profile_for_user(user)
    return profile.role if profile else ""


def get_self_profile_for_user(user):
    profile = profile_for_user(user)
    if not profile:
        return {
            "found": False,
            "answer": "I could not find an active portal profile for this session.",
        }

    full_name = display_name(profile)
    role_label = profile.get_role_display()
    identifier_field = Profile.ROLE_IDENTIFIER_FIELDS.get(profile.role)
    identifier = getattr(profile, identifier_field, "") if identifier_field else ""
    parts = [
        f"You are signed in as {full_name}",
        f"username {profile.user.username}",
        f"role {role_label}",
    ]
    if profile.user.email:
        parts.append(f"email {profile.user.email}")
    if identifier:
        parts.append(f"portal ID {identifier}")

    return {
        "found": True,
        "answer": ", ".join(parts) + ".",
        "data": {
            "name": full_name,
            "username": profile.user.username,
            "email": profile.user.email,
            "role": profile.role,
            "role_label": role_label,
            "portal_id": identifier,
        },
    }


def _aware_datetime(day, value):
    combined = datetime.combine(day, value)
    if timezone.is_naive(combined):
        return timezone.make_aware(combined, timezone.get_current_timezone())
    return combined


def _next_meeting_start(meeting, now):
    local_now = timezone.localtime(now)
    if meeting.meeting_date:
        starts_at = _aware_datetime(meeting.meeting_date, meeting.start_time)
        return starts_at if starts_at >= local_now else None

    days_ahead = (meeting.day_of_week - local_now.isoweekday()) % 7
    meeting_day = local_now.date() + timedelta(days=days_ahead)
    starts_at = _aware_datetime(meeting_day, meeting.start_time)
    if starts_at < local_now:
        starts_at = _aware_datetime(meeting_day + timedelta(days=7), meeting.start_time)
    return starts_at


def _meeting_location(meeting):
    if meeting.venue_id:
        building = getattr(meeting.venue, "building", None)
        if building:
            return f"{building.name} - {meeting.venue.name}"
        return meeting.venue.name
    if meeting.room_id:
        return str(meeting.room)
    return "Venue to be confirmed"


def _meeting_payload(meeting, starts_at):
    return {
        "id": meeting.id,
        "title": f"{meeting.offering.course.code} {meeting.get_class_type_display()}",
        "course_code": meeting.offering.course.code,
        "course_title": meeting.offering.course.title,
        "section": meeting.offering.section,
        "class_type": meeting.get_class_type_display(),
        "topic": meeting.topic,
        "starts_at": timezone.localtime(starts_at).isoformat(),
        "ends_at": timezone.localtime(_aware_datetime(starts_at.date(), meeting.end_time)).isoformat(),
        "day": starts_at.strftime("%A"),
        "location": _meeting_location(meeting),
        "lecturer": display_name(meeting.lecturer),
    }


def _student_meetings(user):
    student = get_student_profile(user)
    if not student:
        return []
    enrollments = (
        Enrollment.objects.select_related(
            "offering",
            "offering__course",
            "tutorial_group",
            "lab_group",
        )
        .filter(student=student, completed_at__isnull=True)
        .order_by("offering__course__code")
    )
    meetings = []
    for enrollment in enrollments:
        meetings.extend(
            selected_class_meetings(
                enrollment.offering,
                enrollment.tutorial_group,
                enrollment.lab_group,
            )
        )
    return meetings


def _teacher_meetings(user):
    teacher = get_teacher_profile(user)
    if not teacher:
        return []
    offerings = teacher_offerings(teacher)
    return list(
        ClassMeeting.objects.select_related(
            "offering",
            "offering__course",
            "lecturer",
            "lecturer__user",
            "room",
            "venue",
            "venue__building",
        )
        .filter(
            Q(lecturer=teacher) | Q(offering__in=offerings),
            status__in=ACTIVE_CLASS_STATUSES,
        )
        .distinct()
        .order_by("meeting_date", "day_of_week", "start_time")
    )


def _meeting_rows_for_user(user):
    role = current_role(user)
    if role == Profile.ROLE_STUDENT:
        meetings = _student_meetings(user)
    elif role == Profile.ROLE_TEACHER:
        meetings = _teacher_meetings(user)
    else:
        return []

    now = timezone.now()
    rows = []
    for meeting in meetings:
        starts_at = _next_meeting_start(meeting, now)
        if starts_at:
            rows.append((starts_at, meeting))
    rows.sort(key=lambda item: (item[0], item[1].offering.course.code, item[1].start_time))
    return rows


def get_next_class_for_user(user):
    rows = _meeting_rows_for_user(user)
    if not rows:
        return {
            "found": False,
            "answer": "I could not find an upcoming class in your current timetable.",
        }
    starts_at, meeting = rows[0]
    payload = _meeting_payload(meeting, starts_at)
    return {
        "found": True,
        "data": payload,
        "answer": (
            f"Your next class is {payload['course_code']} - {payload['course_title']} "
            f"on {payload['day']} at {starts_at.strftime('%H:%M')} in {payload['location']}."
        ),
    }


def get_today_classes_for_user(user):
    today = timezone.localdate()
    rows = [
        _meeting_payload(meeting, starts_at)
        for starts_at, meeting in _meeting_rows_for_user(user)
        if starts_at.date() == today
    ]
    if not rows:
        return {
            "found": False,
            "answer": "I could not find any remaining classes for you today.",
            "data": [],
        }
    summary = "; ".join(
        f"{row['course_code']} at {row['starts_at'][11:16]} ({row['location']})"
        for row in rows[:5]
    )
    return {
        "found": True,
        "answer": f"Your remaining classes today: {summary}.",
        "data": rows,
    }


def get_weekly_timetable_for_user(user):
    role = current_role(user)
    if role == Profile.ROLE_STUDENT:
        payload = student_calendar_payload(user)
    elif role == Profile.ROLE_TEACHER:
        payload = teacher_calendar_payload(user)
    else:
        return {
            "found": False,
            "answer": "Timetable answers are available for student and teacher accounts.",
        }
    count = payload.get("schedule", {}).get("count", 0)
    return {
        "found": True,
        "answer": f"I found {count} timetable and calendar events for your account.",
        "data": payload.get("schedule", {}),
    }


def _assignment_payload(assignment):
    return {
        "id": assignment.id,
        "title": assignment.title,
        "course_code": assignment.offering.course.code,
        "course_title": assignment.offering.course.title,
        "section": assignment.offering.section,
        "due_date": timezone.localtime(assignment.due_date).isoformat()
        if assignment.due_date
        else None,
        "status": assignment.status,
    }


def _assignments_for_user(user):
    role = current_role(user)
    if role == Profile.ROLE_STUDENT:
        student = get_student_profile(user)
        return student_assignments(student)
    if role == Profile.ROLE_TEACHER:
        teacher = get_teacher_profile(user)
        return Assignment.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
        ).filter(offering__in=teacher_offerings(teacher))
    return Assignment.objects.none()


def get_next_deadline_for_user(user):
    now = timezone.now()
    assignment = (
        _assignments_for_user(user)
        .filter(due_date__gte=now, due_date__isnull=False)
        .exclude(status__in=[Assignment.STATUS_DRAFT, Assignment.STATUS_ARCHIVED])
        .order_by("due_date", "title")
        .first()
    )
    if not assignment:
        return {
            "found": False,
            "answer": "I could not find an upcoming assignment deadline for your account.",
        }
    payload = _assignment_payload(assignment)
    due_at = timezone.localtime(assignment.due_date)
    return {
        "found": True,
        "data": payload,
        "answer": (
            f"Your next deadline is {assignment.title} for "
            f"{assignment.offering.course.code} - {assignment.offering.course.title}. "
            f"It is due on {due_at.strftime('%A, %d %B %Y at %H:%M')}."
        ),
    }


def get_upcoming_assignments_for_user(user):
    now = timezone.now()
    assignments = list(
        _assignments_for_user(user)
        .filter(due_date__gte=now, due_date__isnull=False)
        .exclude(status__in=[Assignment.STATUS_DRAFT, Assignment.STATUS_ARCHIVED])
        .order_by("due_date", "title")[:5]
    )
    if not assignments:
        return {
            "found": False,
            "answer": "I could not find upcoming assignments for your account.",
            "data": [],
        }
    summary = "; ".join(
        f"{item.offering.course.code}: {item.title} ({timezone.localtime(item.due_date).strftime('%d %b %H:%M')})"
        for item in assignments
    )
    return {
        "found": True,
        "answer": f"Your upcoming assignments are: {summary}.",
        "data": [_assignment_payload(item) for item in assignments],
    }


def get_current_courses_for_user(user):
    role = current_role(user)
    courses = []
    if role == Profile.ROLE_STUDENT:
        student = get_student_profile(user)
        enrollments = (
            Enrollment.objects.select_related("offering", "offering__course", "offering__semester")
            .filter(student=student, completed_at__isnull=True)
            .order_by("offering__course__code", "offering__section")
        )
        courses = [
            {
                "course_code": enrollment.offering.course.code,
                "course_title": enrollment.offering.course.title,
                "section": enrollment.offering.section,
                "semester": enrollment.offering.semester.name,
            }
            for enrollment in enrollments
        ]
    elif role == Profile.ROLE_TEACHER:
        teacher = get_teacher_profile(user)
        offerings = teacher_offerings(teacher).filter(semester__is_active=True)
        courses = [
            {
                "course_code": offering.course.code,
                "course_title": offering.course.title,
                "section": offering.section,
                "semester": offering.semester.name,
            }
            for offering in offerings
        ]

    if not courses:
        return {
            "found": False,
            "answer": "I could not find current courses for your account.",
            "data": [],
        }
    summary = "; ".join(
        f"{course['course_code']} - {course['course_title']}"
        for course in courses[:6]
    )
    return {
        "found": True,
        "answer": f"Your current courses are: {summary}.",
        "data": courses,
    }


def _clean_text(value, limit=260):
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = " ".join(text.split())
    return text[:limit].rstrip()


def _source(title, source_type, url=""):
    return {"title": title, "type": source_type, "url": url}


def public_context_for_question(question):
    q = question.lower()
    sources = []
    snippets = []

    if "news" in q:
        rows = list(published_news()[:3])
        snippets = [f"{item.title}: {_clean_text(item.summary or item.body)}" for item in rows]
        sources = [_source(item.title, "news", f"/news/{item.slug}") for item in rows]
    elif "event" in q:
        rows = list(published_events()[:3])
        snippets = [
            f"{item.title}: {timezone.localtime(item.starts_at).strftime('%d %b %Y %H:%M')} {item.location}".strip()
            for item in rows
        ]
        sources = [_source(item.title, "event", f"/events/{item.slug}") for item in rows]
    elif "announcement" in q:
        rows = list(public_announcements()[:3])
        snippets = [f"{item.title}: {_clean_text(item.body)}" for item in rows]
        sources = [_source(item.title, "announcement", "/news") for item in rows]
    elif "official" in q or "link" in q:
        rows = list(public_official_links()[:5])
        snippets = [f"{item.title}: {item.url}" for item in rows]
        sources = [_source(item.title, "official_link", item.url) for item in rows]
    else:
        route = "/"
        if "admission" in q or "apply" in q:
            route = "/admissions"
        elif "program" in q or "programme" in q or "course" in q:
            route = "/programmes"
        elif "school" in q or "academic" in q:
            route = "/schools"
        elif "service" in q:
            route = "/services"
        elif "contact" in q or "support" in q:
            route = "/contact"
        page = get_public_page(route_path=route)
        if page:
            snippets = [f"{page.title}: {_clean_text(page.summary or page.body)}"]
            sources = [_source(page.title, "public_page", page.route_path or route)]

    return {"snippets": snippets, "sources": sources}


def public_directory_email_answer(question):
    search = re.sub(
        r"(?i)\b(what|is|the|email|address|of|for|please|can|you|tell|me|find|give|show|contact)\b",
        " ",
        question,
    )
    search = re.sub(r"[^A-Za-z0-9 .'-]", " ", search)
    search = " ".join(search.split())
    queryset = public_models.PublicDirectoryEntry.objects.filter(
        is_active=True,
        email__gt="",
    )
    if search:
        queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
    matches = list(queryset.order_by("entry_type", "sort_order", "name")[:3])
    if not matches:
        return {
            "found": False,
            "answer": "I could not find a public directory email for that name.",
            "sources": [_source("Public directory", "public_directory", "/directories")],
        }
    lines = [f"{item.name}: {item.email}" for item in matches]
    return {
        "found": True,
        "answer": "Public directory email: " + "; ".join(lines) + ".",
        "data": [{"name": item.name, "email": item.email, "url": item.url} for item in matches],
        "sources": [_source("Public directory", "public_directory", "/directories")],
    }
