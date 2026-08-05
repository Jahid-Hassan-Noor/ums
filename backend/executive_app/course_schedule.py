from datetime import date, time
from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from admin_app import models
from core.common.profiles import get_executive_profile, profile_display_name
from admin_app.serializers import (
    CourseSerializer,
    SemesterSerializer,
    VenueSerializer,
)
from executive_app.models import ExecutiveUnitAssignment, TimetableSlot


ACTIVE_MEETING_STATUSES = {
    models.ClassMeeting.STATUS_IMPORTED,
    models.ClassMeeting.STATUS_SCHEDULED,
}


def get_executive_scope(profile):
    if not profile:
        return {"kind": None, "unit": None}

    scopes = []
    if profile.school_id:
        scopes.append(("school", profile.school))
    if profile.center_id:
        scopes.append(("center", profile.center))
    if profile.unit_id:
        if profile.unit.school_id:
            scopes.append(("school", profile.unit.school))
        if profile.unit.center_id:
            scopes.append(("center", profile.unit.center))

    today = timezone.localdate()
    assignments = (
        ExecutiveUnitAssignment.objects.select_related("school", "center")
        .filter(executive=profile, is_active=True)
        .filter(Q(ends_on__isnull=True) | Q(ends_on__gte=today))
    )
    for assignment in assignments:
        if assignment.school_id:
            scopes.append(("school", assignment.school))
        if assignment.center_id:
            scopes.append(("center", assignment.center))

    unique_scopes = {}
    for kind, unit in scopes:
        if unit:
            unique_scopes[(kind, unit.id)] = (kind, unit)

    if len(unique_scopes) > 1:
        raise ValueError("Executive accounts can only be assigned to one school or centre.")

    if not unique_scopes:
        return {"kind": None, "unit": None}

    kind, unit = next(iter(unique_scopes.values()))
    return {"kind": kind, "unit": unit}


def scope_payload(scope):
    unit = scope.get("unit")
    kind = scope.get("kind")
    academic_center = bool(kind == "center" and unit and unit.is_academic_center())
    semester_workflows = scope_supports_academic_workflows(scope)
    return {
        "kind": kind,
        "id": unit.id if unit else None,
        "code": unit.code if unit else "",
        "name": unit.name if unit else "Unassigned",
        "academic_center": academic_center,
        "academic_workflows": semester_workflows,
        "semester_workflows": semester_workflows,
        "academic_calendar_mode": unit.academic_calendar_mode if kind == "center" and unit else "",
        "semester_calendar_group": unit.effective_semester_calendar_group()
        if kind == "center" and unit and unit.uses_semester_calendar()
        else "",
    }


def scope_supports_academic_workflows(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return False
    if kind == "school":
        return True
    return unit.uses_semester_calendar()


def non_academic_scope_response(scope):
    unit = scope.get("unit")
    if scope.get("kind") == "center" and unit and unit.is_academic_center():
        detail = (
            f"{unit.name} is configured as a whole-year academic centre. "
            "Semester course, class schedule, and registration workflows are available only for schools and semester-based academic centres."
        )
    else:
        detail = (
            "This centre is configured as non-academic. "
            "Course, class schedule, and registration workflows are available only for schools and semester-based academic centres."
        )
    return {
        "detail": detail,
        "scope": scope_payload(scope),
    }


def course_scope_filter(scope, prefix=""):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return Q(pk__in=[])

    field = f"{prefix}{kind}"
    program_field = f"{prefix}program__{kind}"
    department_field = f"{prefix}department__{kind}"
    return (
        Q(**{field: unit})
        | Q(**{f"{field}__isnull": True, program_field: unit})
        | Q(**{f"{field}__isnull": True, department_field: unit})
    )


def courses_for_scope(scope):
    return (
        models.Course.objects.select_related("school", "center", "program", "department")
        .filter(course_scope_filter(scope))
        .order_by("code")
    )


def offerings_for_scope(scope):
    return (
        models.CourseOffering.objects.select_related(
            "course",
            "course__school",
            "course__center",
            "semester",
            "instructor",
            "instructor__user",
        )
        .prefetch_related(
            "eligible_schools",
            "eligible_centers",
            "class_meetings__venue__building",
            "class_meetings__lecturer__user",
            "class_meetings__tutorial_group",
            "class_meetings__lab_group",
            "tutorial_groups__lab_groups",
        )
        .filter(course_scope_filter(scope, "course__"))
        .order_by("-created_at")
    )


def teachers_for_scope(scope):
    qs = models.Profile.objects.filter(
        role=models.Profile.ROLE_TEACHER,
        is_active=True,
    ).select_related(
        "user",
        "teacher_detail",
        "teacher_detail__school",
        "teacher_detail__center",
    ).prefetch_related("teacher_scope_assignments")
    kind = scope.get("kind")
    unit = scope.get("unit")
    if kind and unit:
        qs = qs.filter(
            Q(**{f"teacher_detail__{kind}": unit})
            | Q(**{f"teacher_scope_assignments__{kind}": unit})
        ).distinct()
    return qs.order_by("user__first_name", "user__last_name", "user__username")


def teachers_payload(scope):
    return [
        {
            "id": profile.id,
            "name": profile_display_name(profile),
            "staff_id": profile.staff_id,
            "designation": profile.designation,
        }
        for profile in teachers_for_scope(scope)
    ]


def class_type_payload():
    return [
        {"value": value, "label": label}
        for value, label in models.ClassMeeting.CLASS_TYPE_CHOICES
    ]


def parse_time(value):
    try:
        return time.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def parse_positive_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def format_time(value):
    return value.strftime("%H:%M") if value else ""


def times_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def day_label(day_of_week):
    return dict(TimetableSlot.DAY_CHOICES).get(day_of_week, "")


def validate_class_type(value):
    valid_values = {choice[0] for choice in models.ClassMeeting.CLASS_TYPE_CHOICES}
    return value if value in valid_values else None


def resolve_venue(venue_id):
    return (
        models.Venue.objects.select_related("building")
        .filter(pk=venue_id, is_active=True)
        .first()
    )


def resolve_teacher(lecturer_id):
    return (
        models.Profile.objects.select_related("user")
        .filter(pk=lecturer_id, role=models.Profile.ROLE_TEACHER, is_active=True)
        .first()
    )


def meeting_payload_error(index, message):
    return f"Class #{index}: {message}"


def parse_meeting_payload(raw_meeting, index, default_lecturer_id=None, require_date=False):
    if not isinstance(raw_meeting, dict):
        return None, meeting_payload_error(index, "invalid class details.")

    meeting_date = None
    day_of_week = None
    if require_date:
        meeting_date = parse_date(str(raw_meeting.get("meeting_date") or ""))
        if not meeting_date:
            return None, meeting_payload_error(index, "select the week date for this class.")
        day_of_week = meeting_date.isoweekday()
    else:
        try:
            day_of_week = int(raw_meeting.get("day_of_week"))
        except (TypeError, ValueError):
            return None, meeting_payload_error(index, "select a valid class day.")
        if day_of_week not in {choice[0] for choice in TimetableSlot.DAY_CHOICES}:
            return None, meeting_payload_error(index, "select a valid class day.")

    start_time = parse_time(raw_meeting.get("start_time"))
    end_time = parse_time(raw_meeting.get("end_time"))
    if not start_time or not end_time:
        return None, meeting_payload_error(index, "select a valid start and end time.")
    if start_time >= end_time:
        return None, meeting_payload_error(index, "end time must be after start time.")

    venue_id = raw_meeting.get("venue_id")
    if not venue_id:
        return None, meeting_payload_error(index, "select a venue.")
    venue = resolve_venue(venue_id)
    if not venue:
        return None, meeting_payload_error(index, "selected venue is unavailable.")

    lecturer_id = raw_meeting.get("lecturer_id") or default_lecturer_id
    if not lecturer_id:
        return None, meeting_payload_error(index, "select a lecturer.")
    lecturer = resolve_teacher(lecturer_id)
    if not lecturer:
        return None, meeting_payload_error(index, "selected lecturer is unavailable.")

    class_type = validate_class_type(raw_meeting.get("class_type"))
    if not class_type:
        return None, meeting_payload_error(index, "select lecture class or lab class.")

    return (
        {
            "meeting_date": meeting_date,
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
            "venue": venue,
            "lecturer": lecturer,
            "class_type": class_type,
            "tutorial_group_code": str(
                raw_meeting.get("tutorial_group_code")
                or raw_meeting.get("tutorial_group")
                or ""
            ).strip(),
            "lab_group_code": str(
                raw_meeting.get("lab_group_code")
                or raw_meeting.get("lab_group")
                or ""
            ).strip(),
        },
        None,
    )


def _candidate_label(candidate):
    offering = candidate.offering
    return f"{offering.course.code} {offering.section}".strip()


def find_conflicts(
    *,
    semester,
    day_of_week,
    start_time,
    end_time,
    venue,
    lecturer,
    meeting_date=None,
    exclude_meeting_ids=None,
):
    exclude_meeting_ids = set(exclude_meeting_ids or [])
    conflict_filter = Q()
    if venue:
        conflict_filter |= Q(venue=venue)
    if lecturer:
        conflict_filter |= Q(lecturer=lecturer)
    if not conflict_filter:
        return []

    qs = (
        models.ClassMeeting.objects.select_related(
            "offering",
            "offering__course",
            "venue",
            "venue__building",
            "lecturer",
            "lecturer__user",
        )
        .filter(semester=semester, day_of_week=day_of_week, status__in=ACTIVE_MEETING_STATUSES)
        .filter(conflict_filter)
        .exclude(pk__in=exclude_meeting_ids)
    )
    if meeting_date:
        qs = qs.filter(Q(meeting_date__isnull=True) | Q(meeting_date=meeting_date))

    conflicts = []
    for candidate in qs:
        if not times_overlap(start_time, end_time, candidate.start_time, candidate.end_time):
            continue

        reasons = []
        if venue and candidate.venue_id == venue.id:
            reasons.append(f"venue {venue.name}")
        if lecturer and candidate.lecturer_id == lecturer.id:
            reasons.append(f"lecturer {profile_display_name(lecturer)}")

        conflicts.append(
            {
                "meeting_id": candidate.id,
                "course": _candidate_label(candidate),
                "day": day_label(candidate.day_of_week),
                "time": f"{format_time(candidate.start_time)}-{format_time(candidate.end_time)}",
                "reasons": reasons,
            }
        )

    return conflicts


def conflict_message(conflicts):
    conflict = conflicts[0]
    reasons = " and ".join(conflict["reasons"]) or "selection"
    return (
        f"{reasons.capitalize()} conflicts with {conflict['course']} "
        f"on {conflict['day']} at {conflict['time']}."
    )


def validate_internal_conflicts(meetings):
    for index, meeting in enumerate(meetings):
        for other in meetings[index + 1 :]:
            if meeting["day_of_week"] != other["day_of_week"]:
                continue
            if not times_overlap(
                meeting["start_time"],
                meeting["end_time"],
                other["start_time"],
                other["end_time"],
            ):
                continue
            if meeting["venue"].id == other["venue"].id:
                return f"Venue {meeting['venue'].name} is used twice at overlapping times."
            if meeting["lecturer"].id == other["lecturer"].id:
                return f"Lecturer {profile_display_name(meeting['lecturer'])} has overlapping class slots."
    return None


def validate_external_conflicts(semester, meetings, exclude_meeting_ids=None):
    for meeting in meetings:
        conflicts = find_conflicts(
            semester=semester,
            day_of_week=meeting["day_of_week"],
            start_time=meeting["start_time"],
            end_time=meeting["end_time"],
            venue=meeting["venue"],
            lecturer=meeting["lecturer"],
            meeting_date=meeting.get("meeting_date"),
            exclude_meeting_ids=exclude_meeting_ids,
        )
        if conflicts:
            return conflict_message(conflicts)
    return None


def serialize_instructor(profile):
    if not profile:
        return None
    return {"id": profile.id, "name": profile_display_name(profile)}


def serialize_meeting(meeting, include_course=True):
    venue = meeting.venue
    lecturer = meeting.lecturer
    offering = meeting.offering
    tutorial_group = meeting.tutorial_group
    lab_group = meeting.lab_group
    payload = {
        "id": meeting.id,
        "offering_id": offering.id,
        "semester_id": meeting.semester_id,
        "day_of_week": meeting.day_of_week,
        "day_label": day_label(meeting.day_of_week),
        "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
        "start_time": format_time(meeting.start_time),
        "end_time": format_time(meeting.end_time),
        "lecturer": lecturer.id if lecturer else None,
        "lecturer_detail": (
            {
                "id": lecturer.id,
                "name": profile_display_name(lecturer),
                "staff_id": lecturer.staff_id,
            }
            if lecturer
            else None
        ),
        "venue": venue.id if venue else None,
        "venue_detail": VenueSerializer(venue).data if venue else None,
        "class_type": meeting.class_type,
        "class_type_label": dict(models.ClassMeeting.CLASS_TYPE_CHOICES).get(
            meeting.class_type,
            meeting.class_type,
        ),
        "tutorial_group": tutorial_group.id if tutorial_group else None,
        "tutorial_group_code": tutorial_group.code if tutorial_group else "",
        "lab_group": lab_group.id if lab_group else None,
        "lab_group_code": lab_group.code if lab_group else "",
        "status": meeting.status,
        "topic": meeting.topic,
        "recurring_meeting": meeting.recurring_meeting_id,
        "is_single_week_adjustment": bool(meeting.recurring_meeting_id),
    }
    if include_course:
        payload.update(
            {
                "course": CourseSerializer(offering.course).data,
                "semester": SemesterSerializer(offering.semester).data,
                "section": offering.section,
                "capacity": offering.capacity,
                "instructor": serialize_instructor(offering.instructor),
            }
        )
    return payload


def serialize_tutorial_group(group):
    return {
        "id": group.id,
        "code": group.code,
        "capacity": group.capacity,
        "description": group.description,
        "is_active": group.is_active,
        "lab_groups": [
            {
                "id": lab_group.id,
                "code": lab_group.code,
                "capacity": lab_group.capacity,
                "description": lab_group.description,
                "is_active": lab_group.is_active,
            }
            for lab_group in group.lab_groups.all()
        ],
    }


def serialize_offering(offering):
    recurring_meetings = [
        meeting
        for meeting in offering.class_meetings.all()
        if not meeting.recurring_meeting_id
    ]
    return {
        "id": offering.id,
        "course": CourseSerializer(offering.course).data,
        "semester": SemesterSerializer(offering.semester).data,
        "instructor": serialize_instructor(offering.instructor),
        "section": offering.section,
        "capacity": offering.capacity,
        "is_active": offering.is_active,
        "eligible_schools": [
            {"id": school.id, "code": school.code, "name": school.name}
            for school in offering.eligible_schools.all()
        ],
        "eligible_centers": [
            {"id": center.id, "code": center.code, "name": center.name}
            for center in offering.eligible_centers.all()
        ],
        "tutorial_groups": [
            serialize_tutorial_group(group)
            for group in offering.tutorial_groups.all()
        ],
        "meetings": [serialize_meeting(meeting, include_course=False) for meeting in recurring_meetings],
    }


def normalize_group_code(value, default):
    code = str(value or "").strip().upper()
    return code or default


def create_groups_for_offering(offering, group_payloads=None):
    group_payloads = group_payloads if isinstance(group_payloads, list) else []
    if not group_payloads:
        group_payloads = [
            {
                "code": offering.section or "C1",
                "capacity": offering.capacity,
                "lab_groups": (
                    [{"code": "A", "capacity": offering.capacity}]
                    if offering.course.has_lab
                    else []
                ),
            }
        ]

    tutorial_groups = []
    for index, payload in enumerate(group_payloads, start=1):
        if not isinstance(payload, dict):
            continue
        code = normalize_group_code(payload.get("code"), f"C{index}")
        capacity = parse_positive_int(payload.get("capacity"), default=offering.capacity)
        tutorial_group = models.CourseTutorialGroup.objects.create(
            offering=offering,
            code=code,
            capacity=capacity or offering.capacity,
            description=str(payload.get("description", "")).strip(),
        )
        tutorial_groups.append(tutorial_group)

        lab_payloads = payload.get("lab_groups", [])
        if not isinstance(lab_payloads, list):
            lab_payloads = []
        if offering.course.has_lab and not lab_payloads:
            lab_payloads = [{"code": "A", "capacity": tutorial_group.capacity}]
        for lab_index, lab_payload in enumerate(lab_payloads, start=1):
            if not isinstance(lab_payload, dict):
                continue
            models.CourseLabGroup.objects.create(
                tutorial_group=tutorial_group,
                code=normalize_group_code(lab_payload.get("code"), chr(64 + lab_index)),
                capacity=parse_positive_int(lab_payload.get("capacity"), default=tutorial_group.capacity)
                or tutorial_group.capacity,
                description=str(lab_payload.get("description", "")).strip(),
            )

    return tutorial_groups


def resolve_meeting_groups(offering, meeting_data, default_tutorial_group=None):
    tutorial_group = None
    if meeting_data.get("tutorial_group_code"):
        tutorial_group = offering.tutorial_groups.filter(
            code__iexact=meeting_data["tutorial_group_code"],
            is_active=True,
        ).first()
        if not tutorial_group:
            return None, None, f"Tutorial group {meeting_data['tutorial_group_code']} does not exist."
    else:
        tutorial_group = default_tutorial_group or offering.tutorial_groups.filter(is_active=True).order_by("code").first()

    lab_group = None
    if meeting_data["class_type"] == models.ClassMeeting.CLASS_TYPE_LAB:
        if not offering.course.has_lab:
            return None, None, "Lab classes can only be scheduled for courses marked as having lab classes."
        if not tutorial_group:
            return None, None, "Select a tutorial group before scheduling a lab class."
        if meeting_data.get("lab_group_code"):
            lab_group = tutorial_group.lab_groups.filter(
                code__iexact=meeting_data["lab_group_code"],
                is_active=True,
            ).first()
            if not lab_group:
                return None, None, f"Lab group {meeting_data['lab_group_code']} does not exist."
        else:
            lab_group = tutorial_group.lab_groups.filter(is_active=True).order_by("code").first()
        if not lab_group:
            return None, None, "Courses with lab classes require at least one lab group."

    return tutorial_group, lab_group, None


def schedule_rows_for_scope(scope):
    return (
        models.ClassMeeting.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "offering__instructor",
            "offering__instructor__user",
            "semester",
            "venue",
            "venue__building",
            "lecturer",
            "lecturer__user",
            "tutorial_group",
            "lab_group",
            "recurring_meeting",
        )
        .filter(offering__in=offerings_for_scope(scope))
        .order_by("meeting_date", "day_of_week", "start_time", "offering__course__code")
    )


def _xlsx_cell(column, row_index, value):
    cell_ref = f"{column}{row_index}"
    return (
        f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(str(value or ""))}'
        "</t></is></c>"
    )


def build_schedule_xlsx(meetings):
    rows = [
        [
            "Course Code",
            "Course Title",
            "Section",
            "Semester",
            "Class Type",
            "Tutorial Group",
            "Lab Group",
            "Day",
            "Date",
            "Start",
            "End",
            "Venue",
            "Lecturer",
            "Schedule Scope",
        ]
    ]
    for meeting in meetings:
        offering = meeting.offering
        venue = meeting.venue
        venue_name = ""
        if venue:
            venue_name = f"{venue.building.name} - {venue.name}" if venue.building_id else venue.name
        rows.append(
            [
                offering.course.code,
                offering.course.title,
                offering.section,
                offering.semester.name,
                dict(models.ClassMeeting.CLASS_TYPE_CHOICES).get(meeting.class_type, meeting.class_type),
                meeting.tutorial_group.code if meeting.tutorial_group_id else "",
                meeting.lab_group.code if meeting.lab_group_id else "",
                day_label(meeting.day_of_week),
                meeting.meeting_date.isoformat() if meeting.meeting_date else "",
                format_time(meeting.start_time),
                format_time(meeting.end_time),
                venue_name,
                profile_display_name(meeting.lecturer),
                "Single week" if meeting.recurring_meeting_id else "Semester",
            ]
        )

    sheet_rows = []
    columns = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(_xlsx_cell(columns[index], row_index, value) for index, value in enumerate(row))
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        + "".join(sheet_rows)
        + "</sheetData></worksheet>"
    )

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Schedule" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    output.seek(0)
    return output.getvalue()
