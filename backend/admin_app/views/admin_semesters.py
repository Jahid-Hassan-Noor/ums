from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.semester_notifications import notify_semester_event
from admin_app.settings_registry import setting_value
from admin_app.serializers import (
    IELTSSessionSerializer,
    SemesterHolidaySerializer,
    SemesterSerializer,
)
from student_app.models import RegistrationPeriod
from student_app.serializers import RegistrationPeriodSerializer


UGP_2025_2026_REFERENCE = [
    {
        "name": "Semester 1, Session 2025/2026",
        "academic_session": "2025/2026",
        "semester_type": models.Semester.TYPE_LONG,
        "calendar_group": models.Semester.CALENDAR_UNDERGRADUATE,
        "start_date": "2025-10-27",
        "end_date": "2026-02-27",
        "teaching_periods": [
            {"starts_on": "2025-10-27", "ends_on": "2025-12-19", "weeks": 8},
            {"starts_on": "2025-12-29", "ends_on": "2026-02-06", "weeks": 6},
        ],
        "mid_semester_break_starts_on": "2025-12-20",
        "mid_semester_break_ends_on": "2025-12-28",
        "revision_starts_on": "2026-02-07",
        "revision_ends_on": "2026-02-15",
        "examination_starts_on": "2026-02-16",
        "examination_ends_on": "2026-02-27",
        "inter_semester_break_starts_on": "2026-02-28",
        "inter_semester_break_ends_on": "2026-03-22",
        "registration_periods": [
            {
                "title": "Course Pre-Registration",
                "phase": RegistrationPeriod.PHASE_COURSE_REGISTRATION,
                "opens_at": "2025-10-20T00:00:00",
                "closes_at": "2025-10-24T23:59:59",
            },
            {
                "title": "Add and Drop Courses",
                "phase": RegistrationPeriod.PHASE_ADD_DROP,
                "opens_at": "2025-10-27T00:00:00",
                "closes_at": "2025-11-09T23:59:59",
            },
            {
                "title": "Drop Courses",
                "phase": RegistrationPeriod.PHASE_DROP_ONLY,
                "opens_at": "2025-11-10T00:00:00",
                "closes_at": "2025-12-07T23:59:59",
            },
        ],
        "holidays": [
            {"name": "Christmas", "starts_on": "2025-12-25"},
            {"name": "Israk and Mikraj", "starts_on": "2026-01-16"},
            {"name": "Thaipusam", "starts_on": "2026-02-01"},
            {"name": "Chinese New Year", "starts_on": "2026-02-17", "ends_on": "2026-02-18"},
            {"name": "First Day of Ramadhan", "starts_on": "2026-02-18"},
            {"name": "Eidul Fitri", "starts_on": "2026-03-20", "ends_on": "2026-03-21"},
        ],
        "notes": [
            "Course registration: 27 October 2025, Day 1 Week 1.",
            "Add/drop: Week 1 until Week 2.",
            "Extended drop: Week 3 until Week 6.",
            "Course pre-registration for Semester 2: Week 12 to Week 15.",
        ],
    },
    {
        "name": "Semester 2, Session 2025/2026",
        "academic_session": "2025/2026",
        "semester_type": models.Semester.TYPE_LONG,
        "calendar_group": models.Semester.CALENDAR_UNDERGRADUATE,
        "start_date": "2026-03-23",
        "end_date": "2026-07-17",
        "teaching_periods": [
            {"starts_on": "2026-03-23", "ends_on": "2026-05-08", "weeks": 7},
            {"starts_on": "2026-05-11", "ends_on": "2026-06-26", "weeks": 7},
        ],
        "revision_starts_on": "2026-06-27",
        "revision_ends_on": "2026-07-05",
        "examination_starts_on": "2026-07-06",
        "examination_ends_on": "2026-07-17",
        "inter_semester_break_starts_on": "2026-07-18",
        "inter_semester_break_ends_on": "2026-08-02",
        "registration_periods": [
            {
                "title": "Course Pre-Registration",
                "phase": RegistrationPeriod.PHASE_COURSE_REGISTRATION,
                "opens_at": "2026-01-12T00:00:00",
                "closes_at": "2026-02-06T23:59:59",
            },
            {
                "title": "Add and Drop Courses",
                "phase": RegistrationPeriod.PHASE_ADD_DROP,
                "opens_at": "2026-03-23T00:00:00",
                "closes_at": "2026-04-05T23:59:59",
            },
            {
                "title": "Drop Courses",
                "phase": RegistrationPeriod.PHASE_DROP_ONLY,
                "opens_at": "2026-04-06T00:00:00",
                "closes_at": "2026-05-03T23:59:59",
            },
        ],
        "holidays": [
            {"name": "Labour Day", "starts_on": "2026-05-01"},
            {"name": "Eidul Adha", "starts_on": "2026-05-27", "ends_on": "2026-05-28"},
            {"name": "Agong's Birthday", "starts_on": "2026-06-01"},
            {"name": "Muharam New Year", "starts_on": "2026-06-17"},
        ],
        "notes": [
            "Course registration: 23 March 2026, Day 1 Week 1.",
            "Add/drop: Week 1 until Week 2.",
            "Extended drop: Week 3 until Week 6.",
            "Course pre-registration for Semester 3: Week 12 to Week 15.",
        ],
    },
    {
        "name": "Semester 3, Session 2025/2026",
        "academic_session": "2025/2026",
        "semester_type": models.Semester.TYPE_SHORT,
        "calendar_group": models.Semester.CALENDAR_UNDERGRADUATE,
        "start_date": "2026-08-03",
        "end_date": "2026-10-02",
        "teaching_periods": [
            {"starts_on": "2026-08-03", "ends_on": "2026-09-18", "weeks": 7},
        ],
        "revision_starts_on": "2026-09-19",
        "revision_ends_on": "2026-09-27",
        "examination_starts_on": "2026-09-28",
        "examination_ends_on": "2026-10-02",
        "inter_semester_break_starts_on": "2026-10-03",
        "inter_semester_break_ends_on": "2026-10-25",
        "registration_periods": [
            {
                "title": "Course Pre-Registration",
                "phase": RegistrationPeriod.PHASE_COURSE_REGISTRATION,
                "opens_at": "2026-06-08T00:00:00",
                "closes_at": "2026-07-03T23:59:59",
            },
            {
                "title": "Add and Drop Courses",
                "phase": RegistrationPeriod.PHASE_ADD_DROP,
                "opens_at": "2026-08-03T00:00:00",
                "closes_at": "2026-08-16T23:59:59",
            },
            {
                "title": "Drop Courses",
                "phase": RegistrationPeriod.PHASE_DROP_ONLY,
                "opens_at": "2026-08-17T00:00:00",
                "closes_at": "2026-09-13T23:59:59",
            },
        ],
        "holidays": [
            {"name": "The Prophet Muhamad's Birthday", "starts_on": "2026-08-26"},
            {"name": "National Day", "starts_on": "2026-08-31"},
            {"name": "Malaysia Day", "starts_on": "2026-09-16"},
        ],
        "notes": [
            "Revision period: 19 September 2026 to 27 September 2026.",
            "Examination period: 28 September 2026 to 02 October 2026.",
            "Semester 1, Session 2026/2027 commences on 26 October 2026.",
        ],
    },
]


SEMESTER_DATE_FIELDS = (
    "mid_semester_break_starts_on",
    "mid_semester_break_ends_on",
    "revision_starts_on",
    "revision_ends_on",
    "examination_starts_on",
    "examination_ends_on",
    "inter_semester_break_starts_on",
    "inter_semester_break_ends_on",
)
UMS_TIME_ZONE = ZoneInfo("Asia/Kuala_Lumpur")


def _admin_profile(user):
    return models.Profile.objects.filter(user=user, role=models.Profile.ROLE_ADMIN, is_active=True).first()


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_aware_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(str(value))
    if not parsed:
        parsed_date = parse_date(str(value))
        if parsed_date:
            parsed = datetime.combine(parsed_date, time.min)
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, UMS_TIME_ZONE)
    return parsed


def _day_bounds(day, end=False):
    value = datetime.combine(day, time.max if end else time.min)
    return timezone.make_aware(value, UMS_TIME_ZONE) if timezone.is_naive(value) else value


def _default_registration_periods(start_date):
    return [
        {
            "title": "Course Pre-Registration",
            "phase": RegistrationPeriod.PHASE_COURSE_REGISTRATION,
            "opens_at": _day_bounds(start_date - timedelta(days=7)),
            "closes_at": _day_bounds(start_date - timedelta(days=1), end=True),
        },
        {
            "title": "Add and Drop Courses",
            "phase": RegistrationPeriod.PHASE_ADD_DROP,
            "opens_at": _day_bounds(start_date),
            "closes_at": _day_bounds(start_date + timedelta(days=13), end=True),
        },
        {
            "title": "Drop Courses",
            "phase": RegistrationPeriod.PHASE_DROP_ONLY,
            "opens_at": _day_bounds(start_date + timedelta(days=14)),
            "closes_at": _day_bounds(start_date + timedelta(days=41), end=True),
        },
    ]


def _normalize_teaching_periods(value, start_date, end_date):
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValidationError({"teaching_periods": "Teaching periods must be a list."})

    periods = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValidationError({"teaching_periods": f"Teaching period {index} is invalid."})
        starts_on = parse_date(str(item.get("starts_on") or ""))
        ends_on = parse_date(str(item.get("ends_on") or ""))
        if not starts_on or not ends_on or starts_on > ends_on:
            raise ValidationError(
                {"teaching_periods": f"Teaching period {index} requires a valid start and end date."}
            )
        if starts_on < start_date or ends_on > end_date:
            raise ValidationError(
                {"teaching_periods": f"Teaching period {index} must fall inside the semester."}
            )
        periods.append(
            {
                "starts_on": starts_on.isoformat(),
                "ends_on": ends_on.isoformat(),
                "weeks": _parse_positive_int(item.get("weeks"), 1),
            }
        )
    return periods


def _normalize_registration_periods(value, start_date):
    raw_periods = value if isinstance(value, list) and value else _default_registration_periods(start_date)
    periods = []
    for item in raw_periods:
        if not isinstance(item, dict):
            continue
        opens_at = item.get("opens_at")
        closes_at = item.get("closes_at")
        opens_at = opens_at if isinstance(opens_at, datetime) else _parse_aware_datetime(opens_at)
        closes_at = closes_at if isinstance(closes_at, datetime) else _parse_aware_datetime(closes_at)
        phase = item.get("phase", RegistrationPeriod.PHASE_COURSE_REGISTRATION)
        if phase not in dict(RegistrationPeriod.PHASE_CHOICES):
            raise ValidationError({"registration_periods": f"Unknown registration phase: {phase}."})
        if not opens_at or not closes_at or opens_at >= closes_at:
            raise ValidationError(
                {"registration_periods": "Every registration phase requires a valid opening and closing time."}
            )
        periods.append(
            {
                "title": str(item.get("title", "")).strip()
                or dict(RegistrationPeriod.PHASE_CHOICES)[phase],
                "phase": phase,
                "opens_at": opens_at,
                "closes_at": closes_at,
            }
        )

    if len({item["phase"] for item in periods}) != len(periods):
        raise ValidationError({"registration_periods": "Each registration phase may be configured once."})

    ordered = sorted(periods, key=lambda item: item["opens_at"])
    expected = [
        RegistrationPeriod.PHASE_COURSE_REGISTRATION,
        RegistrationPeriod.PHASE_ADD_DROP,
        RegistrationPeriod.PHASE_DROP_ONLY,
    ]
    if [item["phase"] for item in ordered] != expected:
        raise ValidationError(
            {
                "registration_periods": (
                    "Registration phases must run in this order: pre-registration, add/drop, drop only."
                )
            }
        )
    for previous, current in zip(ordered, ordered[1:]):
        if previous["closes_at"] >= current["opens_at"]:
            raise ValidationError({"registration_periods": "Registration phases may not overlap."})
    return ordered


def _semester_payload(data):
    start_date = parse_date(str(data.get("start_date") or ""))
    end_date = parse_date(str(data.get("end_date") or ""))
    if not start_date or not end_date:
        raise ValidationError({"detail": "Semester start_date and end_date are required."})
    if start_date > end_date:
        raise ValidationError({"end_date": "Semester end_date must be after start_date."})

    semester_type = data.get(
        "semester_type",
        setting_value("academic", "default_semester_type"),
    )
    payload = {
        "name": str(data.get("name", "")).strip(),
        "academic_session": str(
            data.get(
                "academic_session",
                setting_value("academic", "default_academic_session"),
            )
        ).strip(),
        "semester_type": semester_type,
        "calendar_group": data.get("calendar_group", models.Semester.CALENDAR_UNDERGRADUATE),
        "starting_week": _parse_positive_int(data.get("starting_week"), 1),
        "start_date": start_date,
        "end_date": end_date,
        "teaching_periods": _normalize_teaching_periods(data.get("teaching_periods"), start_date, end_date),
        "course_offering_opens_at": _parse_aware_datetime(data.get("course_offering_opens_at")),
        "course_offering_closes_at": _parse_aware_datetime(data.get("course_offering_closes_at")),
        "course_selection_closes_at": _parse_aware_datetime(data.get("course_selection_closes_at")),
        "max_credit_hours": _parse_positive_int(
            data.get("max_credit_hours"),
            setting_value("academic", "registration_max_credit_hours"),
        ),
        "default_classes_per_week": _parse_positive_int(
            data.get("default_classes_per_week"),
            2 if semester_type == models.Semester.TYPE_SHORT else 1,
        ),
        "notes": str(data.get("notes", "")).strip(),
    }
    for field in SEMESTER_DATE_FIELDS:
        payload[field] = parse_date(str(data.get(field) or "")) or None
    if not payload["name"]:
        raise ValidationError({"name": "Semester name is required."})
    return payload


def _semester_request_parts(data, activate=False):
    payload = _semester_payload(data)
    periods = _normalize_registration_periods(data.get("registration_periods"), payload["start_date"])
    if (
        payload["course_offering_closes_at"]
        and payload["course_offering_closes_at"] >= periods[0]["opens_at"]
    ):
        raise ValidationError(
            {
                "course_offering_closes_at": (
                    "Course offering must close before course pre-registration opens."
                )
            }
        )
    if activate and payload["end_date"] < timezone.localdate():
        raise ValidationError({"detail": "A historical semester plan cannot be started."})
    holidays = data.get("holidays", [])
    return payload, periods, holidays if isinstance(holidays, list) else []


def _save_semester_relations(semester, holidays, periods, admin_profile):
    for holiday_data in holidays:
        if not isinstance(holiday_data, dict):
            continue
        holiday_start = parse_date(str(holiday_data.get("starts_on") or ""))
        if not holiday_start:
            continue
        holiday = models.SemesterHoliday(
            semester=semester,
            name=str(holiday_data.get("name", "")).strip() or "Semester holiday",
            starts_on=holiday_start,
            ends_on=parse_date(str(holiday_data.get("ends_on") or "")),
            description=str(holiday_data.get("description", "")).strip(),
            is_active=True,
        )
        holiday.full_clean()
        holiday.save()

    for item in periods:
        period = RegistrationPeriod(
            semester=semester,
            title=item["title"],
            phase=item["phase"],
            opens_at=item["opens_at"],
            closes_at=item["closes_at"],
            created_by=admin_profile,
        )
        period.full_clean()
        period.save()


def _semester_status(semester):
    if semester.is_active:
        return "active"
    if semester.end_date and semester.end_date < timezone.localdate():
        return "completed"
    return "planned"


def _serialize_semester(semester, active_groups=None):
    active_groups = active_groups or set()
    is_historical = bool(semester.end_date and semester.end_date < timezone.localdate())
    return {
        **SemesterSerializer(semester).data,
        "status": _semester_status(semester),
        "expected_weeks": 9 if semester.semester_type == models.Semester.TYPE_SHORT else 17,
        "can_start": (
            not semester.is_active
            and not is_historical
            and semester.calendar_group not in active_groups
        ),
        "holidays": SemesterHolidaySerializer(semester.holidays.all(), many=True).data,
        "registration_periods": RegistrationPeriodSerializer(
            RegistrationPeriod.objects.filter(semester=semester).order_by("opens_at"),
            many=True,
        ).data,
    }


def _validation_response(exc):
    detail = exc.message_dict if hasattr(exc, "message_dict") else str(exc)
    return Response(detail, status=status.HTTP_400_BAD_REQUEST)


class AdminSemesters(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        semesters = list(
            models.Semester.objects.prefetch_related("holidays")
            .all()
            .order_by("-start_date", "-created_at")
        )
        active_groups = {semester.calendar_group for semester in semesters if semester.is_active}
        ielts_sessions = models.IELTSSession.objects.select_related("center").all()
        centers = models.Center.objects.filter(center_type=models.Center.CENTER_ACADEMIC, is_active=True).order_by("code")
        return Response(
            {
                "title": "Academic Calendar",
                "section": "admin",
                "calendar_reference": UGP_2025_2026_REFERENCE,
                "semester_types": [
                    {"value": value, "label": label}
                    for value, label in models.Semester.TYPE_CHOICES
                ],
                "calendar_groups": [
                    {"value": value, "label": label}
                    for value, label in models.Semester.CALENDAR_CHOICES
                ],
                "registration_phases": [
                    {"value": value, "label": label}
                    for value, label in RegistrationPeriod.PHASE_CHOICES
                ],
                "summary": {
                    "total": len(semesters),
                    "active": sum(1 for semester in semesters if semester.is_active),
                    "undergraduate": sum(
                        1
                        for semester in semesters
                        if semester.calendar_group == models.Semester.CALENDAR_UNDERGRADUATE
                    ),
                    "foundation": sum(
                        1
                        for semester in semesters
                        if semester.calendar_group == models.Semester.CALENDAR_FOUNDATION
                    ),
                },
                "semesters": [
                    _serialize_semester(semester, active_groups=active_groups)
                    for semester in semesters
                ],
                "ielts_sessions": IELTSSessionSerializer(ielts_sessions, many=True).data,
                "academic_centers": [
                    {"id": center.id, "code": center.code, "name": center.name}
                    for center in centers
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        action = str(request.data.get("action", "start_semester")).strip()
        if action == "create_ielts_session":
            return self._create_ielts_session(request)
        if action == "create_semester":
            return self._create_semester(request, activate=False)
        if action == "update_semester":
            return self._update_semester(request)
        if action == "close_semester":
            return self._close_semester(request)
        if action == "start_semester" and request.data.get("semester_id"):
            return self._activate_semester(request)
        if action == "start_semester":
            return self._create_semester(request, activate=True)
        return Response({"detail": "Unknown semester action."}, status=status.HTTP_400_BAD_REQUEST)

    def _create_ielts_session(self, request):
        academic_session = str(request.data.get("academic_session", "")).strip()
        if models.IELTSSession.objects.filter(academic_session=academic_session).count() >= 2:
            return Response(
                {"detail": "LC may have at most two IELTS exam sessions in an academic year."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = IELTSSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            session = models.IELTSSession(**serializer.validated_data)
            session.full_clean()
            session.save()
        except ValidationError as exc:
            return _validation_response(exc)
        return Response(
            {
                "message": "IELTS session created successfully.",
                "ielts_session": IELTSSessionSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def _create_semester(self, request, activate):
        try:
            payload, periods, holidays = _semester_request_parts(request.data, activate=activate)
        except ValidationError as exc:
            return _validation_response(exc)

        admin_profile = _admin_profile(request.user)

        try:
            with transaction.atomic():
                if activate and models.Semester.objects.select_for_update().filter(
                    calendar_group=payload["calendar_group"],
                    is_active=True,
                ).exists():
                    raise ValidationError(
                        {
                            "detail": (
                                "Another semester is already running for this calendar group. "
                                "Create this semester as a plan or close the running semester first."
                            )
                        }
                    )

                semester = models.Semester(**payload, is_active=activate)
                semester.full_clean()
                semester.save()

                _save_semester_relations(semester, holidays, periods, admin_profile)
        except ValidationError as exc:
            return _validation_response(exc)
        if activate:
            notify_semester_event(
                semester,
                admin_profile,
                event_type="semesters.started",
                verb=f"{semester.name} has started.",
            )

        return Response(
            {
                "message": "Semester started successfully." if activate else "Semester plan created successfully.",
                "semester": _serialize_semester(
                    semester,
                    active_groups={semester.calendar_group} if activate else set(),
                ),
            },
            status=status.HTTP_201_CREATED,
        )

    def _update_semester(self, request):
        try:
            payload, periods, holidays = _semester_request_parts(request.data)
        except ValidationError as exc:
            return _validation_response(exc)

        admin_profile = _admin_profile(request.user)
        try:
            with transaction.atomic():
                semester = models.Semester.objects.select_for_update().filter(
                    pk=request.data.get("semester_id")
                ).first()
                if not semester:
                    return Response({"detail": "Semester not found."}, status=status.HTTP_404_NOT_FOUND)
                if semester.is_active:
                    raise ValidationError(
                        {"detail": "Close the running semester before changing its calendar."}
                    )
                for field, value in payload.items():
                    setattr(semester, field, value)
                semester.full_clean()
                semester.save()
                semester.holidays.all().delete()
                RegistrationPeriod.objects.filter(semester=semester).delete()
                _save_semester_relations(semester, holidays, periods, admin_profile)
        except ValidationError as exc:
            return _validation_response(exc)
        notify_semester_event(
            semester,
            admin_profile,
            event_type="semesters.updated",
            verb=f"{semester.name} plan was updated.",
        )

        return Response(
            {
                "message": "Semester plan updated successfully.",
                "semester": _serialize_semester(semester),
            },
            status=status.HTTP_200_OK,
        )

    def _activate_semester(self, request):
        try:
            with transaction.atomic():
                semester = models.Semester.objects.select_for_update().filter(
                    pk=request.data.get("semester_id")
                ).first()
                if not semester:
                    return Response({"detail": "Semester not found."}, status=status.HTTP_404_NOT_FOUND)
                if semester.is_active:
                    return Response(
                        {
                            "message": "Semester is already active.",
                            "semester": _serialize_semester(semester, {semester.calendar_group}),
                        },
                        status=status.HTTP_200_OK,
                    )
                if semester.end_date and semester.end_date < timezone.localdate():
                    raise ValidationError({"detail": "A historical semester plan cannot be started."})
                if models.Semester.objects.select_for_update().filter(
                    calendar_group=semester.calendar_group,
                    is_active=True,
                ).exclude(pk=semester.pk).exists():
                    raise ValidationError(
                        {
                            "detail": (
                                "Another semester is already running for this calendar group. "
                                "Close it before starting this plan."
                            )
                        }
                    )
                semester.is_active = True
                semester.full_clean()
                semester.save(update_fields=["is_active", "updated_at"])
        except ValidationError as exc:
            return _validation_response(exc)
        notify_semester_event(
            semester,
            _admin_profile(request.user),
            event_type="semesters.started",
            verb=f"{semester.name} has started.",
        )

        return Response(
            {
                "message": "Semester started successfully.",
                "semester": _serialize_semester(semester, {semester.calendar_group}),
            },
            status=status.HTTP_200_OK,
        )

    def _close_semester(self, request):
        semester = models.Semester.objects.filter(pk=request.data.get("semester_id")).first()
        if not semester:
            return Response({"detail": "Semester not found."}, status=status.HTTP_404_NOT_FOUND)
        semester.is_active = False
        semester.save(update_fields=["is_active", "updated_at"])
        notify_semester_event(
            semester,
            _admin_profile(request.user),
            event_type="semesters.closed",
            verb=f"{semester.name} has closed.",
        )
        return Response(
            {
                "message": "Semester closed successfully.",
                "semester": _serialize_semester(semester),
            },
            status=status.HTTP_200_OK,
        )
