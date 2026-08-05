from datetime import datetime, time, timedelta

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
from admin_app.settings_registry import institution_timezone, setting_value
from admin_app.serializers import (
    AcademicSessionSerializer,
    SemesterConfigurationSerializer,
    SemesterHolidaySerializer,
    SemesterSerializer,
)
from student_app.models import RegistrationPeriod
from student_app.serializers import RegistrationPeriodSerializer


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


def _admin_profile(user):
    return models.Profile.objects.filter(user=user, role=models.Profile.ROLE_ADMIN, is_active=True).first()


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_optional_positive_int(value, field):
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError({field: "Provide a valid whole number."}) from None
    if parsed < 1:
        raise ValidationError({field: "Must be at least 1."})
    return parsed


def _parse_aware_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(str(value))
    if not parsed:
        parsed_date = parse_date(str(value))
        if parsed_date:
            parsed = datetime.combine(parsed_date, time.min)
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, institution_timezone())
    return parsed


def _day_bounds(day, end=False):
    value = datetime.combine(day, time.max if end else time.min)
    return timezone.make_aware(value, institution_timezone()) if timezone.is_naive(value) else value


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


def _calendar_group_label(value):
    base_labels = dict(models.Semester.CALENDAR_CHOICES)
    if value in base_labels:
        return base_labels[value]
    center = models.Center.objects.filter(
        semester_calendar_group=value,
        center_type=models.Center.CENTER_ACADEMIC,
        academic_calendar_mode=models.Center.CALENDAR_SEMESTER,
    ).first()
    if center:
        return f"{center.name} semester calendar"
    return value.replace("center:", "").replace("-", " ").title()


def _calendar_group_choices():
    groups = {
        value: label
        for value, label in models.Semester.CALENDAR_CHOICES
    }
    existing_groups = set(
        models.SemesterConfiguration.objects.values_list("calendar_group", flat=True)
    ) | set(models.Semester.objects.values_list("calendar_group", flat=True))
    for value in sorted(existing_groups):
        if value:
            groups.setdefault(value, _calendar_group_label(value))

    semester_centers = models.Center.objects.filter(
        center_type=models.Center.CENTER_ACADEMIC,
        academic_calendar_mode=models.Center.CALENDAR_SEMESTER,
        is_active=True,
    ).order_by("name")
    for center in semester_centers:
        groups[center.effective_semester_calendar_group()] = f"{center.name} semester calendar"

    return [{"value": value, "label": label} for value, label in groups.items()]


def _valid_calendar_group_values():
    return {choice["value"] for choice in _calendar_group_choices()}


def _semester_configuration(calendar_group):
    count = 3
    config, _created = models.SemesterConfiguration.objects.get_or_create(
        calendar_group=calendar_group,
        defaults={
            "semesters_per_year": count,
            "semester_lengths": models.SemesterConfiguration.default_lengths(count),
        },
    )
    if not config.semester_lengths:
        config.semester_lengths = models.SemesterConfiguration.default_lengths(config.semesters_per_year)
        config.full_clean()
        config.save(update_fields=["semester_lengths", "updated_at"])
    return config


def _semester_configurations():
    return [
        _semester_configuration(choice["value"])
        for choice in _calendar_group_choices()
    ]


def _serialize_semester_configuration(config):
    return {
        **SemesterConfigurationSerializer(config).data,
        "calendar_group_label": _calendar_group_label(config.calendar_group),
        "semester_lengths": models.SemesterConfiguration.normalize_lengths(
            config.semester_lengths or models.SemesterConfiguration.default_lengths(config.semesters_per_year),
            config.semesters_per_year,
        ),
    }


def _semester_configuration_payload(data):
    calendar_group = data.get("calendar_group", models.Semester.CALENDAR_UNDERGRADUATE)
    if calendar_group not in _valid_calendar_group_values():
        raise ValidationError({"calendar_group": "Select a valid calendar group."})
    semesters_per_year = _parse_optional_positive_int(
        data.get("semesters_per_year"),
        "semesters_per_year",
    )
    if semesters_per_year is None:
        raise ValidationError({"semesters_per_year": "Semester count is required."})
    raw_lengths = data.get("semester_lengths")
    if raw_lengths in (None, ""):
        raw_lengths = data.get("semesters")
    if raw_lengths in (None, ""):
        raw_lengths = models.SemesterConfiguration.default_lengths(semesters_per_year)
    semester_lengths = models.SemesterConfiguration.normalize_lengths(raw_lengths, semesters_per_year)
    return {
        "calendar_group": calendar_group,
        "semesters_per_year": semesters_per_year,
        "semester_lengths": semester_lengths,
        "notes": str(data.get("notes", "")).strip(),
    }


def _definition_for_semester(calendar_group, semester_number):
    if not semester_number:
        return None
    config = _semester_configuration(calendar_group)
    return config.definition_for(semester_number)


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

    calendar_group = data.get("calendar_group", models.Semester.CALENDAR_UNDERGRADUATE)
    if calendar_group not in _valid_calendar_group_values():
        raise ValidationError({"calendar_group": "Select a valid calendar group."})
    semester_number = _parse_optional_positive_int(data.get("semester_number"), "semester_number")
    definition = _definition_for_semester(calendar_group, semester_number)
    planned_weeks = _parse_optional_positive_int(data.get("planned_weeks"), "planned_weeks")
    if not planned_weeks and definition:
        planned_weeks = definition["weeks"]
    semester_type = data.get(
        "semester_type",
        definition["semester_type"] if definition else setting_value("academic", "default_semester_type"),
    )
    default_classes_per_week = _parse_positive_int(
        data.get("default_classes_per_week"),
        definition["default_classes_per_week"]
        if definition
        else 2 if semester_type == models.Semester.TYPE_SHORT else 1,
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
        "calendar_group": calendar_group,
        "semester_number": semester_number,
        "planned_weeks": planned_weeks,
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
        "default_classes_per_week": default_classes_per_week,
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


def _expected_weeks(semester, configurations=None):
    if semester.planned_weeks:
        return semester.planned_weeks
    config = (configurations or {}).get(semester.calendar_group)
    definition = config.definition_for(semester.semester_number) if config and semester.semester_number else None
    if definition:
        return definition["weeks"]
    return 9 if semester.semester_type == models.Semester.TYPE_SHORT else 17


def _serialize_semester(semester, active_groups=None, configurations=None):
    active_groups = active_groups or set()
    is_historical = bool(semester.end_date and semester.end_date < timezone.localdate())
    return {
        **SemesterSerializer(semester).data,
        "status": _semester_status(semester),
        "expected_weeks": _expected_weeks(semester, configurations=configurations),
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


def _calendar_setup_warnings(academic_centers, semesters, academic_sessions):
    warnings = []
    semester_groups = {semester.calendar_group for semester in semesters}
    session_center_ids = {session.center_id for session in academic_sessions if session.center_id}
    for center in academic_centers:
        if center.uses_semester_calendar():
            calendar_group = center.effective_semester_calendar_group()
            if calendar_group not in semester_groups:
                warnings.append(
                    {
                        "center_id": center.id,
                        "center_code": center.code,
                        "center_name": center.name,
                        "calendar_mode": center.academic_calendar_mode,
                        "calendar_group": calendar_group,
                        "message": (
                            f"{center.name} is semester-based but has no semester plans yet."
                        ),
                    }
                )
        elif center.academic_calendar_mode == models.Center.CALENDAR_WHOLE_YEAR:
            if center.id not in session_center_ids:
                warnings.append(
                    {
                        "center_id": center.id,
                        "center_code": center.code,
                        "center_name": center.name,
                        "calendar_mode": center.academic_calendar_mode,
                        "calendar_group": "",
                        "message": (
                            f"{center.name} is whole-year but has no academic sessions yet."
                        ),
                    }
                )
    return warnings


class AdminSemesters(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        calendar_groups = _calendar_group_choices()
        semester_configurations = {
            config.calendar_group: config
            for config in _semester_configurations()
        }
        semesters = list(
            models.Semester.objects.prefetch_related("holidays")
            .all()
            .order_by("-start_date", "-created_at")
        )
        active_groups = {semester.calendar_group for semester in semesters if semester.is_active}
        academic_sessions = models.AcademicSession.objects.select_related("center").all()
        academic_centers = models.Center.objects.filter(
            center_type=models.Center.CENTER_ACADEMIC,
            is_active=True,
        ).order_by("code")
        year_round_centers = academic_centers.filter(
            academic_calendar_mode=models.Center.CALENDAR_WHOLE_YEAR,
        )
        group_summary = [
            {
                "value": choice["value"],
                "label": choice["label"],
                "total": sum(1 for semester in semesters if semester.calendar_group == choice["value"]),
                "active": sum(
                    1
                    for semester in semesters
                    if semester.calendar_group == choice["value"] and semester.is_active
                ),
            }
            for choice in calendar_groups
        ]
        return Response(
            {
                "title": "Academic Calendar",
                "section": "admin",
                "calendar_reference": [],
                "semester_configurations": [
                    _serialize_semester_configuration(config)
                    for config in semester_configurations.values()
                ],
                "semester_types": [
                    {"value": value, "label": label}
                    for value, label in models.Semester.TYPE_CHOICES
                ],
                "calendar_groups": calendar_groups,
                "calendar_setup_warnings": _calendar_setup_warnings(
                    academic_centers,
                    semesters,
                    academic_sessions,
                ),
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
                    "by_calendar_group": group_summary,
                },
                "semesters": [
                    _serialize_semester(
                        semester,
                        active_groups=active_groups,
                        configurations=semester_configurations,
                    )
                    for semester in semesters
                ],
                "academic_sessions": AcademicSessionSerializer(academic_sessions, many=True).data,
                "ielts_sessions": AcademicSessionSerializer(academic_sessions, many=True).data,
                "academic_centers": [
                    {
                        "id": center.id,
                        "code": center.code,
                        "name": center.name,
                        "academic_calendar_mode": center.academic_calendar_mode,
                        "semester_calendar_group": center.effective_semester_calendar_group()
                        if center.uses_semester_calendar()
                        else "",
                        "annual_session_limit": center.annual_session_limit,
                    }
                    for center in academic_centers
                ],
                "year_round_centers": [
                    {
                        "id": center.id,
                        "code": center.code,
                        "name": center.name,
                        "annual_session_limit": center.annual_session_limit,
                    }
                    for center in year_round_centers
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        action = str(request.data.get("action", "start_semester")).strip()
        if action in {"create_academic_session", "create_ielts_session"}:
            return self._create_academic_session(request)
        if action == "update_semester_configuration":
            return self._update_semester_configuration(request)
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

    def _update_semester_configuration(self, request):
        try:
            payload = _semester_configuration_payload(request.data)
        except ValidationError as exc:
            return _validation_response(exc)

        try:
            with transaction.atomic():
                config = models.SemesterConfiguration.objects.select_for_update().filter(
                    calendar_group=payload["calendar_group"],
                ).first()
                if not config:
                    config = models.SemesterConfiguration(calendar_group=payload["calendar_group"])
                config.semesters_per_year = payload["semesters_per_year"]
                config.semester_lengths = payload["semester_lengths"]
                config.notes = payload["notes"]
                config.full_clean()
                config.save()
        except ValidationError as exc:
            return _validation_response(exc)

        return Response(
            {
                "message": "Semester structure updated successfully.",
                "semester_configuration": _serialize_semester_configuration(config),
            },
            status=status.HTTP_200_OK,
        )

    def _create_academic_session(self, request):
        academic_session = str(request.data.get("academic_session", "")).strip()
        center = models.Center.objects.filter(pk=request.data.get("center")).first()
        if not center:
            return Response(
                {"detail": "Select a whole-year academic centre for this session."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            not center.is_academic_center()
            or center.academic_calendar_mode != models.Center.CALENDAR_WHOLE_YEAR
        ):
            return Response(
                {"detail": "Sessions can only be created for whole-year academic centres."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if center.annual_session_limit and models.AcademicSession.objects.filter(
            academic_session=academic_session,
            center=center,
        ).count() >= center.annual_session_limit:
            return Response(
                {
                    "detail": (
                        f"{center.name} may have at most {center.annual_session_limit} "
                        "session(s) in an academic year."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AcademicSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            session = models.AcademicSession(**serializer.validated_data)
            session.full_clean()
            session.save()
        except ValidationError as exc:
            return _validation_response(exc)
        return Response(
            {
                "message": "Academic session created successfully.",
                "academic_session": AcademicSessionSerializer(session).data,
                "ielts_session": AcademicSessionSerializer(session).data,
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
                    configurations={semester.calendar_group: _semester_configuration(semester.calendar_group)},
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
                "semester": _serialize_semester(
                    semester,
                    configurations={semester.calendar_group: _semester_configuration(semester.calendar_group)},
                ),
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
                            "semester": _serialize_semester(
                                semester,
                                {semester.calendar_group},
                                {semester.calendar_group: _semester_configuration(semester.calendar_group)},
                            ),
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
                "semester": _serialize_semester(
                    semester,
                    {semester.calendar_group},
                    {semester.calendar_group: _semester_configuration(semester.calendar_group)},
                ),
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
                "semester": _serialize_semester(
                    semester,
                    configurations={semester.calendar_group: _semester_configuration(semester.calendar_group)},
                ),
            },
            status=status.HTTP_200_OK,
        )
