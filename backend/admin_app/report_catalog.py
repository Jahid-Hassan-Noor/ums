import json
from datetime import date, datetime

from django.utils.dateparse import parse_date

from admin_app import models
from caterer_app.models import CanteenTransaction
from librarian_app.models import Loan
from student_app.models import AttendanceRecord, CourseRegistration, LeaveRequest
from technician_app.models import HelpdeskTicket


REPORT_DEFINITIONS = {
    "academic-directory": {
        "group": "academic",
        "name": "Academic Directory",
        "description": "Schools, centres, departments, programmes, units, and courses.",
        "statuses": ["active", "inactive"],
    },
    "course-offerings": {
        "group": "academic",
        "name": "Course Offerings",
        "description": "Courses offered by semester, section, instructor, and capacity.",
        "statuses": ["active", "inactive"],
    },
    "course-registrations": {
        "group": "academic",
        "name": "Course Registrations",
        "description": "Student registration requests and approval outcomes.",
        "statuses": [choice[0] for choice in CourseRegistration.STATUS_CHOICES],
    },
    "attendance": {
        "group": "academic",
        "name": "Attendance Records",
        "description": "Student attendance outcomes by course and class date.",
        "statuses": [choice[0] for choice in AttendanceRecord.ATTENDANCE_STATUS_CHOICES],
    },
    "leave-requests": {
        "group": "academic",
        "name": "Leave Requests",
        "description": "Student leave requests and review outcomes.",
        "statuses": [choice[0] for choice in LeaveRequest.STATUS_CHOICES],
    },
    "venue-bookings": {
        "group": "operations",
        "name": "Venue Bookings",
        "description": "Venue booking requests, schedules, and decisions.",
        "statuses": [choice[0] for choice in models.VenueBookingRequest.STATUS_CHOICES],
    },
    "hostel-rooms": {
        "group": "operations",
        "name": "Hostel Rooms",
        "description": "Hostel rooms, capacity, and availability status.",
        "statuses": ["active", "inactive"],
    },
    "canteen-transactions": {
        "group": "operations",
        "name": "Canteen Transactions",
        "description": "Canteen spending transactions by student and month.",
        "statuses": [],
    },
    "library-loans": {
        "group": "operations",
        "name": "Library Loans",
        "description": "Book and laptop loans, due dates, and return status.",
        "statuses": [choice[0] for choice in Loan.STATUS_CHOICES],
    },
    "ict-tickets": {
        "group": "operations",
        "name": "ICT Helpdesk Tickets",
        "description": "Helpdesk tickets, assigned technicians, and resolution status.",
        "statuses": [choice[0] for choice in HelpdeskTicket.STATUS_CHOICES],
    },
    "audit-log": {
        "group": "operations",
        "name": "Audit Log",
        "description": "Privileged administrative actions and affected records.",
        "statuses": [],
    },
}


def _profile_name(profile):
    if not profile:
        return ""
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _record(values, *, record_date=None, status="", search=""):
    return {
        "values": values,
        "date": record_date,
        "status": str(status or "").lower(),
        "search": f"{search} {' '.join(str(value or '') for value in values)}".lower(),
    }


def _record_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _filter_records(records, params):
    query = str(params.get("q", "")).strip().lower()
    status = str(params.get("status", "")).strip().lower()
    date_from = parse_date(str(params.get("date_from", "")).strip())
    date_to = parse_date(str(params.get("date_to", "")).strip())

    filtered = []
    for record in records:
        record_date = _record_date(record["date"])
        if query and query not in record["search"]:
            continue
        if status and record["status"] != status:
            continue
        if date_from and record_date and record_date < date_from:
            continue
        if date_to and record_date and record_date > date_to:
            continue
        filtered.append(record["values"])
    return filtered


def _academic_directory():
    headers = ["Type", "Code", "Name", "School", "Centre", "Department", "Status"]
    records = []
    sources = [
        ("School", models.School.objects.all()),
        ("Centre", models.Center.objects.all()),
        ("Department", models.Department.objects.select_related("school", "center")),
        ("Programme", models.Program.objects.select_related("school", "center", "department")),
        ("Unit", models.Unit.objects.select_related("school", "center", "department")),
        ("Course", models.Course.objects.select_related("school", "center", "department")),
    ]
    for label, queryset in sources:
        for item in queryset:
            active = bool(getattr(item, "is_active", True))
            records.append(
                _record(
                    [
                        label,
                        getattr(item, "code", ""),
                        getattr(item, "name", "") or getattr(item, "title", ""),
                        str(getattr(item, "school", "") or ""),
                        str(getattr(item, "center", "") or ""),
                        str(getattr(item, "department", "") or ""),
                        "Active" if active else "Inactive",
                    ],
                    status="active" if active else "inactive",
                )
            )
    return headers, records


def _course_offerings():
    headers = ["Course", "Title", "Semester", "Section", "Instructor", "Capacity", "Status", "Created"]
    records = []
    queryset = models.CourseOffering.objects.select_related("course", "semester", "instructor__user")
    for item in queryset:
        records.append(
            _record(
                [
                    item.course.code,
                    item.course.title,
                    item.semester.name,
                    item.section,
                    _profile_name(item.instructor),
                    item.capacity,
                    "Active" if item.is_active else "Inactive",
                    item.created_at,
                ],
                record_date=item.created_at,
                status="active" if item.is_active else "inactive",
            )
        )
    return headers, records


def _course_registrations():
    headers = ["Student", "Student ID", "Course", "Semester", "Section", "Status", "Manual", "Created"]
    records = []
    queryset = CourseRegistration.objects.select_related(
        "student__user",
        "offering__course",
        "offering__semester",
    )
    for item in queryset:
        records.append(
            _record(
                [
                    _profile_name(item.student),
                    item.student.student_id,
                    item.offering.course.code,
                    item.offering.semester.name,
                    item.offering.section,
                    item.get_status_display(),
                    "Yes" if item.is_manual else "No",
                    item.created_at,
                ],
                record_date=item.created_at,
                status=item.status,
            )
        )
    return headers, records


def _attendance():
    headers = ["Student", "Student ID", "Course", "Class Date", "Status", "Source", "Present", "Marked At"]
    records = []
    queryset = AttendanceRecord.objects.select_related("student__user", "offering__course")
    for item in queryset:
        records.append(
            _record(
                [
                    _profile_name(item.student),
                    item.student.student_id,
                    item.offering.course.code,
                    item.class_date,
                    item.get_attendance_status_display(),
                    item.get_source_display(),
                    "Yes" if item.present else "No",
                    item.marked_at,
                ],
                record_date=item.class_date,
                status=item.attendance_status,
            )
        )
    return headers, records


def _leave_requests():
    headers = ["Student", "Student ID", "Start Date", "End Date", "Status", "Reason", "Reviewed By", "Created"]
    records = []
    queryset = LeaveRequest.objects.select_related("student__user", "reviewed_by__user")
    for item in queryset:
        records.append(
            _record(
                [
                    _profile_name(item.student),
                    item.student.student_id,
                    item.start_date,
                    item.end_date,
                    item.get_status_display(),
                    item.reason,
                    _profile_name(item.reviewed_by),
                    item.created_at,
                ],
                record_date=item.created_at,
                status=item.status,
            )
        )
    return headers, records


def _venue_bookings():
    headers = ["Requester", "Venue", "Type", "Purpose", "Date", "Start", "End", "Status", "Reviewed By"]
    records = []
    queryset = models.VenueBookingRequest.objects.select_related(
        "requester__user",
        "venue",
        "reviewed_by__user",
    )
    for item in queryset:
        records.append(
            _record(
                [
                    _profile_name(item.requester),
                    str(item.venue),
                    item.get_booking_type_display(),
                    item.purpose,
                    item.booking_date,
                    item.start_time,
                    item.end_time,
                    item.get_status_display(),
                    _profile_name(item.reviewed_by),
                ],
                record_date=item.booking_date,
                status=item.status,
            )
        )
    return headers, records


def _hostel_rooms():
    headers = ["Hostel", "Room Code", "Floor", "Room Number", "Capacity", "Status", "Created"]
    records = []
    for item in models.HostelRoom.objects.select_related("hostel"):
        records.append(
            _record(
                [
                    str(item.hostel),
                    item.code,
                    item.floor,
                    item.number,
                    item.capacity,
                    "Active" if item.is_active else "Inactive",
                    item.created_at,
                ],
                record_date=item.created_at,
                status="active" if item.is_active else "inactive",
            )
        )
    return headers, records


def _canteen_transactions():
    headers = ["Student", "Student ID", "Month", "Amount", "Description", "Caterer", "Created"]
    records = []
    queryset = CanteenTransaction.objects.select_related(
        "account__student__user",
        "caterer__user",
    )
    for item in queryset:
        records.append(
            _record(
                [
                    _profile_name(item.account.student),
                    item.account.student.student_id,
                    item.account.month,
                    item.amount,
                    item.description,
                    _profile_name(item.caterer),
                    item.created_at,
                ],
                record_date=item.created_at,
            )
        )
    return headers, records


def _library_loans():
    headers = ["Student", "Student ID", "Asset", "Borrowed", "Due", "Returned", "Status", "Assigned By"]
    records = []
    queryset = Loan.objects.select_related(
        "student__user",
        "book_copy__book",
        "laptop",
        "assigned_by__user",
    )
    for item in queryset:
        asset = str(item.book_copy) if item.book_copy_id else str(item.laptop or "")
        records.append(
            _record(
                [
                    _profile_name(item.student),
                    item.student.student_id,
                    asset,
                    item.borrowed_at,
                    item.due_at,
                    item.returned_at,
                    item.get_status_display(),
                    _profile_name(item.assigned_by),
                ],
                record_date=item.borrowed_at,
                status=item.status,
            )
        )
    return headers, records


def _ict_tickets():
    headers = ["Student", "Student ID", "Category", "Subject", "Location", "Status", "Assigned To", "Created"]
    records = []
    queryset = HelpdeskTicket.objects.select_related("student__user", "assigned_to__user")
    for item in queryset:
        records.append(
            _record(
                [
                    _profile_name(item.student),
                    item.student.student_id,
                    item.get_category_display(),
                    item.subject,
                    item.location,
                    item.get_status_display(),
                    _profile_name(item.assigned_to),
                    item.created_at,
                ],
                record_date=item.created_at,
                status=item.status,
            )
        )
    return headers, records


def _audit_log():
    headers = ["User", "Action", "Object Type", "Object ID", "Details", "Created"]
    records = []
    for item in models.AuditLog.objects.select_related("user__user"):
        records.append(
            _record(
                [
                    _profile_name(item.user),
                    item.action,
                    item.object_type,
                    item.object_id,
                    json.dumps(item.details or {}, ensure_ascii=True),
                    item.created_at,
                ],
                record_date=item.created_at,
            )
        )
    return headers, records


BUILDERS = {
    "academic-directory": _academic_directory,
    "course-offerings": _course_offerings,
    "course-registrations": _course_registrations,
    "attendance": _attendance,
    "leave-requests": _leave_requests,
    "venue-bookings": _venue_bookings,
    "hostel-rooms": _hostel_rooms,
    "canteen-transactions": _canteen_transactions,
    "library-loans": _library_loans,
    "ict-tickets": _ict_tickets,
    "audit-log": _audit_log,
}


def report_catalog():
    return [
        {"key": key, **definition}
        for key, definition in REPORT_DEFINITIONS.items()
    ]


def report_rows(report_type, params):
    definition = REPORT_DEFINITIONS.get(report_type)
    builder = BUILDERS.get(report_type)
    if not definition or not builder:
        raise KeyError(report_type)
    headers, records = builder()
    return definition, [headers, *_filter_records(records, params)]
