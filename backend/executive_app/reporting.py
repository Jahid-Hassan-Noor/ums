from decimal import Decimal, InvalidOperation

from django.db.models import Q

from admin_app import models as admin_models
from applicant_app import models as applicant_models
from student_app.models import TranscriptRecord


def _option(value, label):
    return {"value": str(value), "label": str(label)}


def _display_name(profile):
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _application_map(profile_ids):
    applications = (
        applicant_models.AdmissionApplication.objects.select_related("intake")
        .filter(applicant__profile_id__in=profile_ids)
        .order_by("applicant__profile_id", "-updated_at", "-created_at")
    )
    latest = {}
    for application in applications:
        latest.setdefault(application.applicant.profile_id, application)
    return latest


def _program_for(profile):
    detail = getattr(profile, "student_detail", None)
    return getattr(detail, "program", None) or profile.program


def _students_for_scope(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return admin_models.Profile.objects.none()
    return (
        admin_models.Profile.objects.select_related(
            "user",
            "student_detail",
            "student_detail__program",
        )
        .filter(role=admin_models.Profile.ROLE_STUDENT, is_active=True)
        .filter(
            Q(**{f"student_detail__{kind}": unit})
            | Q(**{f"student_detail__program__{kind}": unit})
        )
        .order_by("user__first_name", "user__last_name", "student_detail__student_id")
    )


def _teachers_for_scope(scope):
    kind = scope.get("kind")
    unit = scope.get("unit")
    if not kind or not unit:
        return admin_models.Profile.objects.none()
    return (
        admin_models.Profile.objects.select_related(
            "user",
            "teacher_detail",
            "teacher_detail__unit",
            "teacher_detail__department",
        )
        .filter(role=admin_models.Profile.ROLE_TEACHER, is_active=True)
        .filter(
            Q(**{f"teacher_detail__{kind}": unit})
            | Q(**{f"teacher_detail__unit__{kind}": unit})
            | Q(**{f"teacher_scope_assignments__{kind}": unit})
        )
        .distinct()
        .order_by("user__first_name", "user__last_name", "user__username")
    )


def student_rows(scope):
    students = list(_students_for_scope(scope))
    applications = _application_map([student.id for student in students])
    rows = []
    for profile in students:
        detail = getattr(profile, "student_detail", None)
        program = _program_for(profile)
        application = applications.get(profile.id)
        intake = application.intake if application and application.intake_id else None
        status = str(getattr(detail, "enrollment_status", "") or "active").strip()
        row = {
            "name": _display_name(profile),
            "username": profile.user.username,
            "email": profile.user.email,
            "student_id": profile.student_id,
            "phone": profile.phone,
            "program_id": program.id if program else None,
            "program": f"{program.code} - {program.name}" if program else "",
            "status": status,
            "current_year": getattr(detail, "current_year", None),
            "intake_id": intake.id if intake else None,
            "intake": intake.title if intake else "",
            "cohort": intake.academic_year if intake else "",
        }
        row["search_text"] = " ".join(str(value or "") for value in row.values()).lower()
        rows.append(row)
    return rows


def filter_student_rows(rows, params):
    query = str(params.get("q", "")).strip().lower()
    program = str(params.get("program", "")).strip()
    status = str(params.get("status", "")).strip()
    current_year = str(params.get("current_year", "")).strip()
    intake = str(params.get("intake", "")).strip()
    cohort = str(params.get("cohort", "")).strip()
    filtered = [
        row
        for row in rows
        if not query or query in row["search_text"]
        if not program or str(row["program_id"] or "") == program
        if not status or row["status"] == status
        if not current_year or str(row["current_year"] or "") == current_year
        if not intake or str(row["intake_id"] or "") == intake
        if not cohort or row["cohort"] == cohort
    ]
    filtered.sort(key=lambda row: (row["name"].lower(), row["student_id"].lower()))
    return filtered


def student_filters(rows):
    return {
        "programs": _unique_options(rows, "program_id", "program"),
        "statuses": [_option(value, value.title()) for value in _unique_values(rows, "status")],
        "current_years": [_option(value, f"Year {value}") for value in _unique_values(rows, "current_year")],
        "intakes": _unique_options(rows, "intake_id", "intake"),
        "cohorts": [_option(value, value) for value in _unique_values(rows, "cohort")],
    }


def teacher_rows(scope):
    profiles = list(_teachers_for_scope(scope))
    rows = []
    for profile in profiles:
        detail = getattr(profile, "teacher_detail", None)
        department = profile.department or getattr(detail, "department", None)
        unit = profile.unit or getattr(detail, "unit", None)
        designation = profile.designation or getattr(detail, "designation", "")
        row = {
            "name": _display_name(profile),
            "username": profile.user.username,
            "email": profile.user.email,
            "staff_id": profile.staff_id,
            "phone": profile.phone,
            "designation": designation,
            "academic_rank": getattr(detail, "academic_rank", ""),
            "specialization": getattr(detail, "specialization", ""),
            "department_id": department.id if department else None,
            "department": f"{department.code} - {department.name}" if department else "",
            "unit_id": unit.id if unit else None,
            "unit": f"{unit.code} - {unit.name}" if unit else "",
            "office_location": getattr(detail, "office_location", ""),
        }
        row["search_text"] = " ".join(str(value or "") for value in row.values()).lower()
        rows.append(row)
    return rows


def filter_teacher_rows(rows, params):
    query = str(params.get("q", "")).strip().lower()
    designation = str(params.get("designation", "")).strip()
    academic_rank = str(params.get("academic_rank", "")).strip()
    department = str(params.get("department", "")).strip()
    unit = str(params.get("unit", "")).strip()
    filtered = [
        row
        for row in rows
        if not query or query in row["search_text"]
        if not designation or row["designation"] == designation
        if not academic_rank or row["academic_rank"] == academic_rank
        if not department or str(row["department_id"] or "") == department
        if not unit or str(row["unit_id"] or "") == unit
    ]
    filtered.sort(key=lambda row: (row["name"].lower(), row["staff_id"].lower()))
    return filtered


def teacher_filters(rows):
    return {
        "designations": [_option(value, value) for value in _unique_values(rows, "designation")],
        "academic_ranks": [_option(value, value) for value in _unique_values(rows, "academic_rank")],
        "departments": _unique_options(rows, "department_id", "department"),
        "units": _unique_options(rows, "unit_id", "unit"),
    }


def result_rows(scope):
    students = list(_students_for_scope(scope))
    applications = _application_map([student.id for student in students])
    records = TranscriptRecord.objects.select_related(
        "student__user",
        "student__student_detail__program",
        "semester",
        "offering__course",
    ).filter(student__in=students, published_at__isnull=False)
    rows = []
    for record in records:
        profile = record.student
        program = _program_for(profile)
        application = applications.get(profile.id)
        intake = application.intake if application and application.intake_id else None
        row = {
            "name": _display_name(profile),
            "student_id": profile.student_id,
            "program_id": program.id if program else None,
            "program": f"{program.code} - {program.name}" if program else "",
            "intake_id": intake.id if intake else None,
            "intake": intake.title if intake else "",
            "cohort": intake.academic_year if intake else "",
            "semester_id": record.semester_id,
            "semester": record.semester.name if record.semester_id else "",
            "course_code": record.course_code
            or (record.offering.course.code if record.offering_id else ""),
            "course_title": record.course_title
            or (record.offering.course.title if record.offering_id else ""),
            "credit_hours": record.credit_hours,
            "score": record.score,
            "grade": record.grade,
            "grade_points": record.grade_points,
            "gpa": record.gpa,
            "cgpa": record.cgpa,
            "published_at": record.published_at,
        }
        row["search_text"] = " ".join(str(value or "") for value in row.values()).lower()
        rows.append(row)
    return rows


def filter_result_rows(rows, params):
    query = str(params.get("q", "")).strip().lower()
    program = str(params.get("program", "")).strip()
    semester = str(params.get("semester", "")).strip()
    intake = str(params.get("intake", "")).strip()
    cohort = str(params.get("cohort", "")).strip()
    minimum_cgpa = _decimal(params.get("minimum_cgpa"))
    maximum_cgpa = _decimal(params.get("maximum_cgpa"))
    filtered = []
    for row in rows:
        cgpa = _decimal(row["cgpa"])
        if query and query not in row["search_text"]:
            continue
        if program and str(row["program_id"] or "") != program:
            continue
        if semester and str(row["semester_id"] or "") != semester:
            continue
        if intake and str(row["intake_id"] or "") != intake:
            continue
        if cohort and row["cohort"] != cohort:
            continue
        if minimum_cgpa is not None and (cgpa is None or cgpa < minimum_cgpa):
            continue
        if maximum_cgpa is not None and (cgpa is None or cgpa > maximum_cgpa):
            continue
        filtered.append(row)
    filtered.sort(
        key=lambda row: (
            row["name"].lower(),
            row["semester"],
            row["course_code"],
        )
    )
    return filtered


def result_filters(rows):
    return {
        "programs": _unique_options(rows, "program_id", "program"),
        "semesters": _unique_options(rows, "semester_id", "semester"),
        "intakes": _unique_options(rows, "intake_id", "intake"),
        "cohorts": [_option(value, value) for value in _unique_values(rows, "cohort")],
    }


def _unique_values(rows, key):
    return sorted({row[key] for row in rows if row.get(key) not in (None, "")}, key=str)


def _unique_options(rows, value_key, label_key):
    values = {
        row[value_key]: row[label_key]
        for row in rows
        if row.get(value_key) not in (None, "") and row.get(label_key)
    }
    return [
        _option(value, label)
        for value, label in sorted(values.items(), key=lambda item: str(item[1]))
    ]


def students_workbook(rows):
    return [
        [
            "Student ID",
            "Name",
            "Username",
            "Email",
            "Phone",
            "Programme",
            "Enrollment Status",
            "Current Year",
            "Intake",
            "Cohort",
        ],
        *[
            [
                row["student_id"],
                row["name"],
                row["username"],
                row["email"],
                row["phone"],
                row["program"],
                row["status"],
                row["current_year"],
                row["intake"],
                row["cohort"],
            ]
            for row in rows
        ],
    ]


def teachers_workbook(rows):
    return [
        [
            "Staff ID",
            "Name",
            "Username",
            "Email",
            "Phone",
            "Designation",
            "Academic Rank",
            "Specialization",
            "Department",
            "Unit",
            "Office",
        ],
        *[
            [
                row["staff_id"],
                row["name"],
                row["username"],
                row["email"],
                row["phone"],
                row["designation"],
                row["academic_rank"],
                row["specialization"],
                row["department"],
                row["unit"],
                row["office_location"],
            ]
            for row in rows
        ],
    ]


def results_workbook(rows):
    return [
        [
            "Student ID",
            "Student",
            "Programme",
            "Intake",
            "Cohort",
            "Semester",
            "Course Code",
            "Course Title",
            "Credit Hours",
            "Score",
            "Grade",
            "Grade Points",
            "GPA",
            "CGPA",
            "Published At",
        ],
        *[
            [
                row["student_id"],
                row["name"],
                row["program"],
                row["intake"],
                row["cohort"],
                row["semester"],
                row["course_code"],
                row["course_title"],
                row["credit_hours"],
                row["score"],
                row["grade"],
                row["grade_points"],
                row["gpa"],
                row["cgpa"],
                row["published_at"],
            ]
            for row in rows
        ],
    ]
