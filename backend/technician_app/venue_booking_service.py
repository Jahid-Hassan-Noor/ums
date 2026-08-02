from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from datetime import timedelta

from admin_app.models import (
    ClassMeeting,
    Profile,
    Venue,
    VenueBookingRequest,
)
from admin_app.settings_registry import setting_value
from core.common.profiles import profile_display_name
from notifications_package.service import notify_profile, notify_profiles


ACTIVE_MEETING_STATUSES = {
    ClassMeeting.STATUS_IMPORTED,
    ClassMeeting.STATUS_SCHEDULED,
}


class BookingConflictError(Exception):
    pass


def times_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def validate_booking_payload(data):
    venue = Venue.objects.select_related("building").filter(
        pk=data.get("venue_id"),
        is_active=True,
    ).first()
    if not venue:
        return None, "Select an active venue."

    booking_type = str(data.get("booking_type") or "").strip().lower()
    if booking_type not in dict(VenueBookingRequest.TYPE_CHOICES):
        return None, "Select event or personal use."

    purpose = str(data.get("purpose") or "").strip()
    if len(purpose) < 3:
        return None, "Provide the purpose of the venue booking."

    explanation = str(data.get("explanation") or "").strip()
    if len(explanation) < 20:
        return None, "Provide a detailed explanation of at least 20 characters."

    booking_date = parse_date(str(data.get("booking_date") or ""))
    if not booking_date:
        return None, "Select a valid booking date."
    if booking_date < timezone.localdate():
        return None, "Venue bookings cannot be requested for a past date."
    minimum_notice = setting_value("workflow", "venue_booking_min_notice_days")
    if booking_date < timezone.localdate() + timedelta(days=minimum_notice):
        return None, f"Venue bookings require at least {minimum_notice} day(s) notice."

    start_time = parse_time(str(data.get("start_time") or ""))
    end_time = parse_time(str(data.get("end_time") or ""))
    if not start_time or not end_time:
        return None, "Select a valid start and end time."
    if start_time >= end_time:
        return None, "End time must be after start time."

    return {
        "venue": venue,
        "booking_type": booking_type,
        "purpose": purpose,
        "explanation": explanation,
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
    }, None


def _meeting_label(meeting):
    course = meeting.offering.course
    return f"{course.code} {course.title}".strip()


def _class_conflict(venue, booking_date, start_time, end_time, *, include_recurring_classes=True):
    dated_meetings = (
        ClassMeeting.objects.select_related("offering", "offering__course")
        .filter(
            venue=venue,
            meeting_date=booking_date,
            status__in=ACTIVE_MEETING_STATUSES,
        )
        .order_by("start_time")
    )
    for meeting in dated_meetings:
        if times_overlap(start_time, end_time, meeting.start_time, meeting.end_time):
            return (
                f"{venue.name} is assigned to class {_meeting_label(meeting)} "
                f"from {meeting.start_time.strftime('%H:%M')} to {meeting.end_time.strftime('%H:%M')}."
            )

    if not include_recurring_classes:
        return None

    adjusted_recurring_ids = ClassMeeting.objects.filter(
        meeting_date=booking_date,
        recurring_meeting__isnull=False,
    ).values_list("recurring_meeting_id", flat=True)
    recurring_meetings = (
        ClassMeeting.objects.select_related("offering", "offering__course", "semester")
        .filter(
            venue=venue,
            meeting_date__isnull=True,
            recurring_meeting__isnull=True,
            day_of_week=booking_date.isoweekday(),
            status__in=ACTIVE_MEETING_STATUSES,
        )
        .exclude(pk__in=adjusted_recurring_ids)
        .filter(
            Q(semester__isnull=True)
            | Q(semester__start_date__isnull=True)
            | Q(semester__start_date__lte=booking_date)
        )
        .filter(
            Q(semester__isnull=True)
            | Q(semester__end_date__isnull=True)
            | Q(semester__end_date__gte=booking_date)
        )
        .order_by("start_time")
    )
    for meeting in recurring_meetings:
        if times_overlap(start_time, end_time, meeting.start_time, meeting.end_time):
            return (
                f"{venue.name} is assigned to class {_meeting_label(meeting)} "
                f"from {meeting.start_time.strftime('%H:%M')} to {meeting.end_time.strftime('%H:%M')}."
            )
    return None


def _approved_booking_conflict(venue, booking_date, start_time, end_time, exclude_request_id=None):
    bookings = VenueBookingRequest.objects.select_related("requester", "requester__user").filter(
        venue=venue,
        booking_date=booking_date,
        status=VenueBookingRequest.STATUS_APPROVED,
    )
    if exclude_request_id:
        bookings = bookings.exclude(pk=exclude_request_id)

    for booking in bookings:
        if times_overlap(start_time, end_time, booking.start_time, booking.end_time):
            return (
                f"{venue.name} is already assigned to {profile_display_name(booking.requester)} "
                f"from {booking.start_time.strftime('%H:%M')} to {booking.end_time.strftime('%H:%M')}."
            )
    return None


def booking_conflict_message(
    venue,
    booking_date,
    start_time,
    end_time,
    exclude_request_id=None,
    *,
    include_final_exams=True,
    include_recurring_classes=True,
):
    conflict = _class_conflict(
        venue,
        booking_date,
        start_time,
        end_time,
        include_recurring_classes=include_recurring_classes,
    ) or _approved_booking_conflict(
        venue,
        booking_date,
        start_time,
        end_time,
        exclude_request_id=exclude_request_id,
    )
    if conflict or not include_final_exams:
        return conflict

    from executive_app.final_exam_schedule import final_exam_venue_conflict_message

    return final_exam_venue_conflict_message(venue, booking_date, start_time, end_time)


def venues_payload():
    return [
        {
            "id": venue.id,
            "code": venue.code,
            "name": venue.name,
            "building": venue.building.name,
            "capacity": venue.capacity,
        }
        for venue in Venue.objects.select_related("building").filter(is_active=True).order_by("building__name", "name")
    ]


def serialize_booking(booking):
    return {
        "id": booking.id,
        "requester": {
            "id": booking.requester_id,
            "name": profile_display_name(booking.requester),
            "role": booking.requester.role,
            "student_id": booking.requester.student_id,
            "staff_id": booking.requester.staff_id,
        },
        "venue": {
            "id": booking.venue_id,
            "code": booking.venue.code,
            "name": booking.venue.name,
            "building": booking.venue.building.name,
            "capacity": booking.venue.capacity,
        },
        "booking_type": booking.booking_type,
        "purpose": booking.purpose,
        "explanation": booking.explanation,
        "booking_date": booking.booking_date.isoformat(),
        "start_time": booking.start_time.strftime("%H:%M"),
        "end_time": booking.end_time.strftime("%H:%M"),
        "status": booking.status,
        "reviewed_by": profile_display_name(booking.reviewed_by),
        "rejection_reason": booking.rejection_reason,
        "reviewed_at": booking.reviewed_at.isoformat() if booking.reviewed_at else None,
        "created_at": booking.created_at.isoformat(),
    }


def bookings_queryset():
    return VenueBookingRequest.objects.select_related(
        "requester",
        "requester__user",
        "venue",
        "venue__building",
        "reviewed_by",
        "reviewed_by__user",
    )


def venue_booking_reviewer_profiles():
    return Profile.objects.filter(role=Profile.ROLE_TECHNICIAN, is_active=True)


@transaction.atomic
def submit_booking(requester, payload):
    conflict = booking_conflict_message(
        payload["venue"],
        payload["booking_date"],
        payload["start_time"],
        payload["end_time"],
    )
    if conflict:
        raise BookingConflictError(conflict)

    booking = VenueBookingRequest.objects.create(requester=requester, **payload)
    if setting_value("notifications", "notify_approvals"):
        notify_profiles(
            venue_booking_reviewer_profiles(),
            actor=requester,
            event_type="venues.booking_requested",
            verb=f"Venue booking requested for {booking.venue.name}",
            data={
                "venue_booking_request_id": booking.id,
                "venue_id": booking.venue_id,
                "booking_date": booking.booking_date.isoformat(),
                "start_time": booking.start_time.strftime("%H:%M"),
                "end_time": booking.end_time.strftime("%H:%M"),
            },
            url="/technician/venue-bookings",
        )
    return booking


@transaction.atomic
def cancel_booking(booking_id, requester):
    booking = (
        VenueBookingRequest.objects.select_for_update()
        .select_related("requester", "requester__user", "venue", "venue__building")
        .filter(pk=booking_id, requester=requester)
        .first()
    )
    if not booking:
        raise ValueError("Venue booking request not found.")
    if booking.status not in {
        VenueBookingRequest.STATUS_PENDING,
        VenueBookingRequest.STATUS_APPROVED,
    }:
        raise ValueError("Only pending or approved venue bookings can be cancelled.")

    booking.status = VenueBookingRequest.STATUS_CANCELLED
    booking.save(update_fields=["status", "updated_at"])
    if setting_value("notifications", "notify_approvals"):
        notify_profiles(
            venue_booking_reviewer_profiles(),
            actor=requester,
            event_type="venues.booking_cancelled",
            verb=f"Venue booking cancelled for {booking.venue.name}",
            data={
                "venue_booking_request_id": booking.id,
                "venue_id": booking.venue_id,
                "booking_date": booking.booking_date.isoformat(),
                "start_time": booking.start_time.strftime("%H:%M"),
                "end_time": booking.end_time.strftime("%H:%M"),
            },
            url="/technician/venue-bookings",
        )
    return booking


@transaction.atomic
def decide_booking(booking_id, reviewer, decision, rejection_reason=""):
    booking = VenueBookingRequest.objects.select_for_update().filter(pk=booking_id).first()
    if not booking:
        raise ValueError("Venue booking request not found.")
    if booking.status != VenueBookingRequest.STATUS_PENDING:
        raise ValueError("Only pending venue booking requests can be reviewed.")

    if decision == VenueBookingRequest.STATUS_APPROVED:
        Venue.objects.select_for_update().get(pk=booking.venue_id)
        conflict = booking_conflict_message(
            booking.venue,
            booking.booking_date,
            booking.start_time,
            booking.end_time,
            exclude_request_id=booking.id,
        )
        if conflict:
            raise BookingConflictError(conflict)
        booking.rejection_reason = ""
    elif decision == VenueBookingRequest.STATUS_REJECTED:
        rejection_reason = rejection_reason.strip()
        if not rejection_reason:
            raise ValueError("A rejection reason is required.")
        booking.rejection_reason = rejection_reason
    else:
        raise ValueError("Decision must be approved or rejected.")

    booking.status = decision
    booking.reviewed_by = reviewer
    booking.reviewed_at = timezone.now()
    booking.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"]
    )
    if setting_value("notifications", "notify_approvals"):
        notify_profile(
            booking.requester,
            actor=reviewer,
            event_type="venues.booking_decided",
            verb=f"Your venue booking for {booking.venue.name} was {decision}.",
            data={
                "venue_booking_request_id": booking.id,
                "decision": decision,
                "rejection_reason": booking.rejection_reason,
            },
            url=f"/{booking.requester.role}/venue-bookings",
        )
    return booking
