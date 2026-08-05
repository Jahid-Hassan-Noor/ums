import secrets
import string
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from admin_app.models import ClassMeeting, Profile
from admin_app.settings_registry import setting_value
from core.common.academic_policy import attendance_qr_ttl_seconds
from core.media_access import protected_media_url
from core.upload_security import (
    ALLOWED_IMAGE_EXTENSIONS_DOTTED,
    image_file_extension,
    image_upload_error,
)
from notifications_package.service import notify_profile, notify_profiles
from student_app.models import AttendanceCodeSubmission, AttendanceRecord, Enrollment
from teacher_app.assignment_service import profile_display_name, teacher_offerings
from teacher_app.models import AttendanceSession


PRESENT_STATUSES = {AttendanceRecord.STATUS_ATTEND, AttendanceRecord.STATUS_LATE}
QR_CODE_LENGTH = 6
QR_CODE_ALPHABET = string.ascii_lowercase + string.digits
MAX_MEDICAL_CERTIFICATE_BYTES = 5 * 1024 * 1024
MEDICAL_CERTIFICATE_EXTENSIONS = frozenset({".pdf"}) | ALLOWED_IMAGE_EXTENSIONS_DOTTED


def qr_ttl_seconds():
    return attendance_qr_ttl_seconds()


def teacher_meetings(profile):
    if not profile:
        return ClassMeeting.objects.none()
    return (
        ClassMeeting.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "lecturer",
            "lecturer__user",
            "tutorial_group",
            "lab_group",
            "venue",
            "venue__building",
        )
        .filter(Q(lecturer=profile) | Q(offering__in=teacher_offerings(profile)))
        .distinct()
        .order_by("day_of_week", "start_time", "offering__course__code")
    )


def teacher_sessions(profile):
    return (
        AttendanceSession.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "class_meeting",
            "class_meeting__tutorial_group",
            "class_meeting__lab_group",
            "created_by",
            "created_by__user",
        )
        .filter(class_meeting__in=teacher_meetings(profile))
        .order_by("-session_date", "-created_at")
    )


def meeting_for_teacher(profile, meeting_id):
    return teacher_meetings(profile).filter(pk=meeting_id).first()


def session_for_teacher(profile, session_id):
    return teacher_sessions(profile).filter(pk=session_id).first()


def parse_clock(value, fallback):
    parsed = parse_time(str(value or ""))
    if parsed:
        return parsed
    if isinstance(fallback, str):
        return parse_time(fallback)
    return fallback


def combine_aware(day, clock):
    dt = datetime.combine(day, clock)
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def enrollment_matches_meeting(enrollment, meeting):
    if meeting.tutorial_group_id and enrollment.tutorial_group_id != meeting.tutorial_group_id:
        return False
    if meeting.lab_group_id and enrollment.lab_group_id != meeting.lab_group_id:
        return False
    return True


def enrollments_for_meeting(meeting):
    enrollments = Enrollment.objects.select_related("student", "student__user").filter(
        offering=meeting.offering,
        completed_at__isnull=True,
    )
    return [enrollment for enrollment in enrollments if enrollment_matches_meeting(enrollment, meeting)]


def notify_meeting_students(meeting, actor, verb, data):
    if not setting_value("notifications", "notify_attendance_warnings"):
        return
    notify_profiles(
        [enrollment.student for enrollment in enrollments_for_meeting(meeting)],
        actor=actor,
        event_type="attendance.class_changed",
        verb=verb,
        data=data,
        url="/student/attendance",
    )


def new_qr_token(session):
    now = timezone.now()
    for _attempt in range(20):
        token = "".join(secrets.choice(QR_CODE_ALPHABET) for _index in range(QR_CODE_LENGTH))
        collision = (
            AttendanceSession.objects.filter(
                status=AttendanceSession.STATUS_OPEN,
                qr_token=token,
                qr_expires_at__gt=now,
            )
            .exclude(pk=session.pk)
            .exists()
        )
        if not collision:
            return token
    return secrets.token_hex(4)[:QR_CODE_LENGTH]


def generate_qr(session):
    session.qr_token = new_qr_token(session)
    session.qr_expires_at = timezone.now() + timedelta(seconds=qr_ttl_seconds())
    session.save(update_fields=["qr_token", "qr_expires_at", "updated_at"])
    return session.qr_token


def refresh_qr_if_needed(session):
    if session.status != AttendanceSession.STATUS_OPEN:
        return session
    if not session.qr_token or not session.qr_expires_at or session.qr_expires_at <= timezone.now():
        generate_qr(session)
        session.refresh_from_db()
    return session


@transaction.atomic
def start_attendance_session(profile, meeting, *, session_date=None, start_time=None, end_time=None):
    session_date = session_date or timezone.localdate()
    actual_start = combine_aware(session_date, parse_clock(start_time, meeting.start_time))
    actual_end = combine_aware(session_date, parse_clock(end_time, meeting.end_time))
    session, _created = AttendanceSession.objects.get_or_create(
        class_meeting=meeting,
        session_date=session_date,
        defaults={
            "offering": meeting.offering,
            "created_by": profile,
        },
    )
    session.offering = meeting.offering
    session.created_by = profile
    session.status = AttendanceSession.STATUS_OPEN
    session.opens_at = timezone.now()
    session.closes_at = None
    session.actual_starts_at = actual_start
    session.actual_ends_at = actual_end
    session.cancellation_reason = ""
    session.save(
        update_fields=[
            "offering",
            "created_by",
            "status",
            "opens_at",
            "closes_at",
            "actual_starts_at",
            "actual_ends_at",
            "cancellation_reason",
            "updated_at",
        ]
    )
    generate_qr(session)
    return session


def close_attendance_session(session):
    session.status = AttendanceSession.STATUS_CLOSED
    session.closes_at = timezone.now()
    session.qr_token = ""
    session.qr_expires_at = timezone.now()
    session.save(update_fields=["status", "closes_at", "qr_token", "qr_expires_at", "updated_at"])
    return session


def meeting_attendance_window(meeting, now=None):
    now = timezone.localtime(now or timezone.now())
    today = now.date()
    if meeting.status == ClassMeeting.STATUS_CANCELLED:
        return {
            "can_open": False,
            "reason": "This class has been cancelled.",
            "starts_at": None,
            "ends_at": None,
        }
    if meeting.meeting_date and meeting.meeting_date != today:
        return {
            "can_open": False,
            "reason": f"This class is scheduled for {meeting.meeting_date.isoformat()}.",
            "starts_at": None,
            "ends_at": None,
        }
    if not meeting.meeting_date and meeting.day_of_week != today.isoweekday():
        return {
            "can_open": False,
            "reason": f"This class runs on {meeting.get_day_of_week_display()}.",
            "starts_at": None,
            "ends_at": None,
        }
    starts_at = combine_aware(today, meeting.start_time)
    ends_at = combine_aware(today, meeting.end_time)
    if now < starts_at:
        reason = f"Attendance opens when class starts at {meeting.start_time.strftime('%H:%M')}."
    elif now > ends_at:
        reason = f"This class ended at {meeting.end_time.strftime('%H:%M')}."
    else:
        reason = "Attendance can be opened now."
    return {
        "can_open": starts_at <= now <= ends_at,
        "reason": reason,
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
    }


def serialize_meeting(meeting):
    return {
        "id": meeting.id,
        "offering_id": meeting.offering_id,
        "course_code": meeting.offering.course.code,
        "course_title": meeting.offering.course.title,
        "semester": meeting.offering.semester.name,
        "day_of_week": meeting.day_of_week,
        "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
        "start_time": meeting.start_time.strftime("%H:%M"),
        "end_time": meeting.end_time.strftime("%H:%M"),
        "tutorial_group": meeting.tutorial_group.code if meeting.tutorial_group_id else "",
        "lab_group": meeting.lab_group.code if meeting.lab_group_id else "",
        "class_type": meeting.class_type,
        "status": meeting.status,
        "venue": meeting.venue.name if meeting.venue_id else "",
        "attendance_window": meeting_attendance_window(meeting),
    }


def serialize_session(session, include_token=False):
    session = refresh_qr_if_needed(session) if include_token else session
    payload = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "offering_id": session.offering_id,
        "course_code": session.offering.course.code,
        "course_title": session.offering.course.title,
        "class_meeting": serialize_meeting(session.class_meeting) if session.class_meeting_id else None,
        "status": session.status,
        "opens_at": session.opens_at.isoformat() if session.opens_at else None,
        "closes_at": session.closes_at.isoformat() if session.closes_at else None,
        "actual_starts_at": session.actual_starts_at.isoformat() if session.actual_starts_at else None,
        "actual_ends_at": session.actual_ends_at.isoformat() if session.actual_ends_at else None,
        "schedule_change_reason": session.schedule_change_reason,
        "cancellation_reason": session.cancellation_reason,
    }
    if include_token:
        payload.update(
            {
                "qr_token": session.qr_token,
                "qr_expires_at": session.qr_expires_at.isoformat() if session.qr_expires_at else None,
                "qr_ttl_seconds": qr_ttl_seconds(),
                "attendance_url_path": f"/class-attendance?code={session.qr_token}" if session.qr_token else "",
            }
        )
    return payload


def eligible_student_for_session(student, session):
    enrollment = Enrollment.objects.select_related("offering").filter(
        student=student,
        offering=session.offering,
        completed_at__isnull=True,
    ).first()
    return bool(enrollment and (not session.class_meeting_id or enrollment_matches_meeting(enrollment, session.class_meeting)))


@transaction.atomic
def submit_qr_attendance(student, *, session, token, ip_address=""):
    if session.status != AttendanceSession.STATUS_OPEN:
        submission_status = AttendanceCodeSubmission.STATUS_REJECTED
        message = "Attendance QR is closed."
    elif not eligible_student_for_session(student, session):
        submission_status = AttendanceCodeSubmission.STATUS_REJECTED
        message = "You are not enrolled in this class group."
    elif not token or token != session.qr_token:
        submission_status = AttendanceCodeSubmission.STATUS_REJECTED
        message = "Invalid attendance QR code."
    elif not session.qr_expires_at or session.qr_expires_at <= timezone.now():
        submission_status = AttendanceCodeSubmission.STATUS_EXPIRED
        message = "Attendance QR code expired. Scan the new QR code."
    elif AttendanceRecord.objects.filter(student=student, attendance_session=session).exists():
        submission_status = AttendanceCodeSubmission.STATUS_DUPLICATE
        message = "Attendance already submitted."
    else:
        submission_status = AttendanceCodeSubmission.STATUS_ACCEPTED
        message = "Attendance submitted."

    submission = AttendanceCodeSubmission.objects.create(
        student=student,
        session=session,
        code=token or "",
        status=submission_status,
        message=message,
        ip_address=ip_address or None,
    )

    if submission_status == AttendanceCodeSubmission.STATUS_ACCEPTED:
        AttendanceRecord.objects.create(
            student=student,
            offering=session.offering,
            attendance_session=session,
            class_date=session.session_date,
            present=True,
            attendance_status=AttendanceRecord.STATUS_ATTEND,
            source=AttendanceRecord.SOURCE_QR,
            submitted_code=token,
            marked_by=session.created_by,
            marked_at=timezone.now(),
        )
    return submission


def manual_mark_attendance(session, student, marker, *, attendance_status, reason="", medical_certificate=None):
    if not eligible_student_for_session(student, session):
        return None, "Student is not enrolled in this class group."
    if attendance_status not in {choice[0] for choice in AttendanceRecord.ATTENDANCE_STATUS_CHOICES}:
        return None, "Select Attend, Late, Absent with reason, or Absent with MC."
    if medical_certificate:
        certificate_error = validate_medical_certificate(medical_certificate)
        if certificate_error:
            return None, certificate_error
    record, _created = AttendanceRecord.objects.get_or_create(
        student=student,
        attendance_session=session,
        defaults={
            "offering": session.offering,
            "class_date": session.session_date,
        },
    )
    record.offering = session.offering
    record.class_date = session.session_date
    record.attendance_status = attendance_status
    record.present = attendance_status in PRESENT_STATUSES
    record.source = AttendanceRecord.SOURCE_MANUAL
    record.reason = reason
    if medical_certificate:
        record.medical_certificate = medical_certificate
    record.marked_by = marker
    record.marked_at = timezone.now()
    record.save()
    return record, None


def validate_medical_certificate(upload):
    extension = f".{image_file_extension(upload)}"
    if extension not in MEDICAL_CERTIFICATE_EXTENSIONS:
        return "Medical certificate must be a PDF or a jpg, jpeg, png, webp, heic, or heif image."
    if upload.size > MAX_MEDICAL_CERTIFICATE_BYTES:
        return "Medical certificate must be 5 MB or smaller."
    if extension in ALLOWED_IMAGE_EXTENSIONS_DOTTED:
        return image_upload_error(
            upload,
            field_label="Medical certificate image",
            max_bytes=MAX_MEDICAL_CERTIFICATE_BYTES,
            max_size_label="5 MB",
        )
    return ""


def reschedule_or_cancel_class(profile, meeting, data):
    meeting_date = parse_date(str(data.get("meeting_date") or "")) or meeting.meeting_date
    target = meeting
    if meeting_date and not meeting.meeting_date:
        target, _created = ClassMeeting.objects.get_or_create(
            recurring_meeting=meeting,
            meeting_date=meeting_date,
            defaults={
                "offering": meeting.offering,
                "semester": meeting.semester,
                "class_group": meeting.class_group,
                "tutorial_group": meeting.tutorial_group,
                "lab_group": meeting.lab_group,
                "day_of_week": meeting_date.isoweekday(),
                "start_time": meeting.start_time,
                "end_time": meeting.end_time,
                "lecturer": meeting.lecturer,
                "room": meeting.room,
                "venue": meeting.venue,
                "class_type": meeting.class_type,
                "status": ClassMeeting.STATUS_SCHEDULED,
            },
        )

    action = str(data.get("action", "reschedule")).lower()
    reason = str(data.get("reason", "")).strip()
    if action == "cancel":
        target.status = ClassMeeting.STATUS_CANCELLED
        target.cancellation_reason = reason
        target.save(update_fields=["status", "cancellation_reason", "updated_at"])
        notify_meeting_students(
            target,
            profile,
            f"{target.offering.course.code} class cancelled.",
            {"class_meeting_id": target.id, "reason": reason, "meeting_date": meeting_date.isoformat() if meeting_date else None},
        )
        return target

    target.start_time = parse_clock(data.get("start_time"), target.start_time)
    target.end_time = parse_clock(data.get("end_time"), target.end_time)
    target.status = ClassMeeting.STATUS_SCHEDULED
    target.schedule_change_reason = reason
    target.save(update_fields=["start_time", "end_time", "status", "schedule_change_reason", "updated_at"])
    notify_meeting_students(
        target,
        profile,
        f"{target.offering.course.code} class time updated.",
        {
            "class_meeting_id": target.id,
            "start_time": target.start_time.strftime("%H:%M"),
            "end_time": target.end_time.strftime("%H:%M"),
            "reason": reason,
            "meeting_date": meeting_date.isoformat() if meeting_date else None,
        },
    )
    return target


def attendance_summary_for_offering(offering, meeting=None):
    sessions = AttendanceSession.objects.filter(offering=offering).exclude(status=AttendanceSession.STATUS_CANCELLED)
    if meeting:
        sessions = sessions.filter(class_meeting=meeting)
    session_count = sessions.count()
    summaries = []
    enrollments = Enrollment.objects.select_related("student", "student__user").filter(
        offering=offering,
        completed_at__isnull=True,
    )
    for enrollment in enrollments:
        records = AttendanceRecord.objects.filter(student=enrollment.student, attendance_session__in=sessions)
        attended = records.filter(attendance_status__in=PRESENT_STATUSES).count()
        percentage = round((attended / session_count) * 100, 2) if session_count else 0
        summaries.append(
            {
                "student_id": enrollment.student_id,
                "student_name": profile_display_name(enrollment.student),
                "ums_id": enrollment.student.student_id,
                "attended": attended,
                "total_classes": session_count,
                "attendance_percentage": percentage,
            }
        )
    return summaries


def enrollment_group_label(enrollment):
    if enrollment.lab_group_id:
        return enrollment.lab_group.code
    if enrollment.tutorial_group_id:
        return enrollment.tutorial_group.code
    return enrollment.offering.section


def attendance_record_payload(session, record):
    if record:
        status = record.attendance_status
        present = record.present
        source = record.source
        reason = record.reason
        medical_certificate = protected_media_url(record.medical_certificate.name) if record.medical_certificate else ""
        marked_at = record.marked_at.isoformat() if record.marked_at else None
        record_id = record.id
    else:
        status = "pending" if session.status == AttendanceSession.STATUS_OPEN else "absent"
        present = False
        source = ""
        reason = ""
        medical_certificate = ""
        marked_at = None
        record_id = None
    meeting = session.class_meeting
    scheduled_start = None
    scheduled_end = None
    if meeting:
        scheduled_start = meeting.start_time.strftime("%H:%M")
        scheduled_end = meeting.end_time.strftime("%H:%M")
    return {
        "id": record_id,
        "session_id": session.id,
        "class_date": session.session_date.isoformat(),
        "start_time": scheduled_start,
        "end_time": scheduled_end,
        "status": status,
        "session_status": session.status,
        "present": present,
        "source": source,
        "reason": reason,
        "medical_certificate": medical_certificate,
        "marked_at": marked_at,
    }


def student_attendance_semesters(student):
    if not student:
        return []
    rows = (
        Enrollment.objects.select_related("offering__semester")
        .filter(student=student)
        .order_by("-offering__semester__is_active", "-offering__semester__start_date", "-offering__semester__created_at")
    )
    semesters = []
    seen = set()
    for enrollment in rows:
        semester = enrollment.offering.semester
        if semester.id in seen:
            continue
        seen.add(semester.id)
        semesters.append(
            {
                "id": semester.id,
                "name": semester.name,
                "academic_session": semester.academic_session,
                "is_active": semester.is_active,
                "start_date": semester.start_date.isoformat() if semester.start_date else None,
                "end_date": semester.end_date.isoformat() if semester.end_date else None,
            }
        )
    return semesters


def student_attendance_semester(student, semester_id=None):
    enrollments = Enrollment.objects.select_related("offering__semester").filter(student=student)
    if semester_id:
        enrollment = enrollments.filter(offering__semester_id=semester_id).first()
        return enrollment.offering.semester if enrollment else None
    enrollment = enrollments.filter(offering__semester__is_active=True).first()
    if enrollment:
        return enrollment.offering.semester
    enrollment = enrollments.order_by("-offering__semester__start_date", "-offering__semester__created_at").first()
    return enrollment.offering.semester if enrollment else None


def student_attendance_summary(student, semester=None):
    enrollments = Enrollment.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
        "tutorial_group",
        "lab_group",
    ).filter(student=student)
    if semester:
        enrollments = enrollments.filter(offering__semester=semester)
    summaries = []
    for enrollment in enrollments:
        sessions = AttendanceSession.objects.select_related("class_meeting").filter(
            offering=enrollment.offering,
        ).exclude(status=AttendanceSession.STATUS_CANCELLED)
        sessions = [
            session
            for session in sessions
            if not session.class_meeting_id or enrollment_matches_meeting(enrollment, session.class_meeting)
        ]
        records = AttendanceRecord.objects.filter(
            student=student,
            attendance_session__in=sessions,
        ).select_related("attendance_session")
        records_by_session = {record.attendance_session_id: record for record in records}
        attended = sum(
            1
            for record in records_by_session.values()
            if record.attendance_status in PRESENT_STATUSES
        )
        late = sum(
            1
            for record in records_by_session.values()
            if record.attendance_status == AttendanceRecord.STATUS_LATE
        )
        total = len(sessions)
        summaries.append(
            {
                "offering_id": enrollment.offering_id,
                "course_code": enrollment.offering.course.code,
                "course_title": enrollment.offering.course.title,
                "semester": enrollment.offering.semester.name,
                "semester_id": enrollment.offering.semester_id,
                "group": enrollment_group_label(enrollment),
                "attended": attended,
                "late": late,
                "absent": max(total - attended, 0),
                "total_classes": total,
                "attendance_percentage": round((attended / total) * 100, 2) if total else 0,
                "records": [
                    attendance_record_payload(session, records_by_session.get(session.id))
                    for session in sorted(sessions, key=lambda item: (item.session_date, item.id), reverse=True)
                ],
            }
        )
    return summaries


def attendance_roster_for_session(session):
    records = {
        record.student_id: record
        for record in AttendanceRecord.objects.filter(attendance_session=session).select_related(
            "student",
            "student__user",
        )
    }
    if session.class_meeting_id:
        enrollments = enrollments_for_meeting(session.class_meeting)
    else:
        enrollments = Enrollment.objects.select_related(
            "student",
            "student__user",
            "offering",
            "tutorial_group",
            "lab_group",
        ).filter(
            offering=session.offering,
            completed_at__isnull=True,
        )
    return [
        {
            "student_id": enrollment.student_id,
            "student_name": profile_display_name(enrollment.student),
            "ums_id": enrollment.student.student_id,
            "group": enrollment_group_label(enrollment),
            "record": attendance_record_payload(session, records.get(enrollment.student_id)),
        }
        for enrollment in enrollments
    ]


def send_low_attendance_warnings(offering, actor, threshold=None, minimum_classes=None):
    if not setting_value("notifications", "notify_attendance_warnings"):
        return []
    threshold = threshold or setting_value("academic", "attendance_threshold_percent")
    minimum_classes = minimum_classes or setting_value(
        "academic",
        "attendance_warning_minimum_classes",
    )
    sent = []
    for summary in attendance_summary_for_offering(offering):
        if summary["total_classes"] < minimum_classes or summary["attendance_percentage"] >= threshold:
            continue
        student = Profile.objects.filter(pk=summary["student_id"]).first()
        if not student:
            continue
        notify_profile(
            student,
            actor=actor,
            event_type="attendance.low_warning",
            verb=f"Attendance warning for {offering.course.code}",
            data={
                "offering_id": offering.id,
                "course_code": offering.course.code,
                "attendance_percentage": summary["attendance_percentage"],
                "threshold": threshold,
            },
            url="/student/attendance/report",
        )
        sent.append(summary)
    return sent
