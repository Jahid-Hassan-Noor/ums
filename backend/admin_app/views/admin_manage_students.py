from collections import defaultdict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.report_exports import completed_xlsx_response
from applicant_app import models as applicant_models
from student_app.models import CourseRegistration, Enrollment, Student


def _display_name(profile):
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _detail_for(profile):
    try:
        return profile.student_detail
    except Student.DoesNotExist:
        return None


def _option(value, label):
    return {"value": str(value), "label": str(label)}


STUDENT_STATUS_LABELS = {
    "active": "Active",
    "dropout": "Dropout",
    "graduated": "Graduated",
    "internship": "Internship",
    "terminated": "Terminated",
}


def _student_status(enrollment_status, is_active):
    normalized = str(enrollment_status or "").strip().lower()
    if "graduat" in normalized:
        return "graduated", "Graduated"
    if "drop" in normalized or "withdraw" in normalized:
        return "dropout", "Dropout"
    if "intern" in normalized:
        return "internship", "Internship"
    if "terminat" in normalized:
        return "terminated", "Terminated"
    if normalized == "active" or is_active:
        return "active", "Active"
    return normalized or "active", enrollment_status or "Active"


def _student_gender(profile, detail, personal):
    candidates = [
        getattr(detail, "gender", ""),
        getattr(detail, "sex", ""),
        getattr(profile, "gender", ""),
        getattr(profile, "sex", ""),
        personal.get("gender") if personal else "",
        personal.get("sex") if personal else "",
    ]
    for candidate in candidates:
        normalized = str(candidate or "").strip().lower()
        if normalized in {"m", "male", "man"}:
            return "male"
        if normalized in {"f", "female", "woman"}:
            return "female"
    return ""


def _student_options():
    return {
        "statuses": [
            _option(value, label)
            for value, label in STUDENT_STATUS_LABELS.items()
        ],
        "programs": [
            {
                "value": str(program.id),
                "label": f"{program.code} - {program.name}",
                "school": program.school_id,
                "center": program.center_id,
                "department": program.department_id,
            }
            for program in models.Program.objects.select_related(
                "school",
                "center",
                "department",
            )
            .filter(is_active=True)
            .order_by("name")
        ],
    }


def _student_profiles():
    return (
        models.Profile.objects.select_related(
            "user",
            "student_detail",
            "student_detail__school",
            "student_detail__center",
            "student_detail__program",
        )
        .filter(role=models.Profile.ROLE_STUDENT)
        .order_by("user__first_name", "user__last_name", "user__username")
    )


def _application_maps(profile_ids):
    applicants = {
        applicant.profile_id: applicant
        for applicant in applicant_models.Applicant.objects.filter(
            profile_id__in=profile_ids
        )
    }
    applications = (
        applicant_models.AdmissionApplication.objects.select_related(
            "applicant",
            "intake",
        )
        .filter(applicant__profile_id__in=profile_ids)
        .order_by("applicant__profile_id", "-updated_at", "-created_at")
    )
    latest_application_by_profile = {}
    for application in applications:
        latest_application_by_profile.setdefault(
            application.applicant.profile_id,
            application,
        )
    return applicants, latest_application_by_profile


def _session_map(profile_ids):
    sessions_by_profile = defaultdict(set)
    registrations = CourseRegistration.objects.filter(
        student_id__in=profile_ids,
        offering__semester__academic_session__gt="",
    ).values_list("student_id", "offering__semester__academic_session")
    enrollments = Enrollment.objects.filter(
        student_id__in=profile_ids,
        offering__semester__academic_session__gt="",
    ).values_list("student_id", "offering__semester__academic_session")

    for profile_id, session in list(registrations) + list(enrollments):
        if session:
            sessions_by_profile[profile_id].add(session)
    return sessions_by_profile


def _student_rows():
    profiles = list(_student_profiles())
    profile_ids = [profile.id for profile in profiles]
    applicants, applications = _application_maps(profile_ids)
    sessions_by_profile = _session_map(profile_ids)
    rows = []

    for profile in profiles:
        detail = _detail_for(profile)
        applicant = applicants.get(profile.id)
        application = applications.get(profile.id)
        personal = (application.personal_information or {}) if application else {}
        intake = application.intake if application and application.intake_id else None
        session_values = sorted(sessions_by_profile.get(profile.id, set()))
        if application and application.intake and application.intake.academic_year:
            session_values = sorted(
                set(session_values) | {application.intake.academic_year}
            )

        student_id = ""
        if detail and detail.student_id:
            student_id = detail.student_id
        elif profile.student_id:
            student_id = profile.student_id

        country = ""
        nationality = ""
        if applicant:
            country = applicant.country_of_residence or applicant.nationality
            nationality = applicant.nationality
        if not country and application:
            country = personal.get("country") or personal.get("country_of_residence") or ""
            nationality = personal.get("nationality") or ""

        enrollment_status = detail.enrollment_status if detail else ""
        gender = _student_gender(profile, detail, personal)
        is_active = bool(profile.is_active and profile.user.is_active)
        student_status, student_status_label = _student_status(
            enrollment_status,
            is_active,
        )

        row = {
            "id": profile.id,
            "user_id": profile.user_id,
            "username": profile.user.username,
            "name": _display_name(profile),
            "email": profile.user.email,
            "student_id": student_id,
            "phone": profile.phone,
            "gender": gender,
            "country": country,
            "nationality": nationality,
            "intake_id": intake.id if intake else None,
            "intake": intake.title if intake else "",
            "intake_code": intake.code if intake else "",
            "session": ", ".join(session_values),
            "session_values": session_values,
            "school": profile.school_id,
            "school_code": profile.school.code if profile.school_id else "",
            "school_name": profile.school.name if profile.school_id else "",
            "center": profile.center_id,
            "center_code": profile.center.code if profile.center_id else "",
            "center_name": profile.center.name if profile.center_id else "",
            "program": profile.program_id,
            "program_code": profile.program.code if profile.program_id else "",
            "program_name": profile.program.name if profile.program_id else "",
            "admission_number": detail.admission_number if detail else "",
            "enrollment_status": enrollment_status,
            "status": student_status,
            "status_label": student_status_label,
            "room": detail.room if detail else "",
            "current_year": detail.current_year if detail else None,
            "is_active": is_active,
        }
        row["search_text"] = " ".join(
            str(value or "")
            for value in [
                row["name"],
                row["username"],
                row["email"],
                row["student_id"],
                row["gender"],
                row["country"],
                row["nationality"],
                row["intake"],
                row["session"],
                row["status_label"],
                row["school_name"],
                row["school_code"],
                row["program_name"],
                row["program_code"],
            ]
        ).lower()
        rows.append(row)
    return rows


def _filter_rows(rows, params):
    query = str(params.get("q", "")).strip().lower()
    country = str(params.get("country", "")).strip()
    intake = str(params.get("intake", "")).strip()
    session = str(params.get("session", "")).strip()
    student_status = str(params.get("status", "")).strip()
    school = str(params.get("school", "")).strip()
    program = str(params.get("program", "")).strip()

    filtered = []
    for row in rows:
        if query and query not in row["search_text"]:
            continue
        if country and row["country"] != country and row["nationality"] != country:
            continue
        if intake and str(row["intake_id"] or "") != intake:
            continue
        if session and session not in row["session_values"]:
            continue
        if student_status and row["status"] != student_status:
            continue
        if school and str(row["school"] or "") != school:
            continue
        if program and str(row["program"] or "") != program:
            continue
        filtered.append(row)

    reverse = str(params.get("sort", "asc")).strip().lower() == "desc"
    filtered.sort(
        key=lambda row: (
            str(row["name"] or "").lower(),
            str(row["student_id"] or "").lower(),
        ),
        reverse=reverse,
    )
    return filtered


def _public_rows(rows):
    return [
        {key: value for key, value in row.items() if key != "search_text"}
        for row in rows
    ]


def _filters(rows):
    countries = sorted(
        {row["country"] for row in rows if row["country"]}
        | {row["nationality"] for row in rows if row["nationality"]}
    )
    intakes = {
        row["intake_id"]: row["intake"]
        for row in rows
        if row["intake_id"] and row["intake"]
    }
    sessions = sorted(
        {session for row in rows for session in row["session_values"] if session}
    )
    return {
        "countries": [_option(country, country) for country in countries],
        "intakes": [
            _option(value, label)
            for value, label in sorted(intakes.items(), key=lambda item: item[1])
        ],
        "sessions": [_option(session, session) for session in sessions],
        "statuses": _student_options()["statuses"],
        "schools": [
            _option(school.id, f"{school.code} - {school.name}")
            for school in models.School.objects.filter(is_active=True).order_by("name")
        ],
        "programs": [
            _option(program.id, f"{program.code} - {program.name}")
            for program in models.Program.objects.filter(is_active=True).order_by("name")
        ],
    }


def _export_response(request, rows, filename):
    headers = [
        "Student ID",
        "Name",
        "Username",
        "Email",
        "Phone",
        "Gender",
        "Country",
        "Nationality",
        "Intake",
        "Session",
        "School",
        "Program",
        "Admission Number",
        "Status",
        "Enrollment Status",
        "Room",
        "Current Year",
        "Active",
    ]
    body = [headers]
    for row in rows:
        body.append(
            [
                row["student_id"],
                row["name"],
                row["username"],
                row["email"],
                row["phone"],
                row["gender"].title() if row["gender"] else "",
                row["country"],
                row["nationality"],
                row["intake"],
                row["session"],
                row["school_name"] or row["school_code"],
                row["program_name"] or row["program_code"],
                row["admission_number"],
                row["status_label"],
                row["enrollment_status"],
                row["room"],
                row["current_year"] or "",
                "Yes" if row["is_active"] else "No",
            ]
        )

    return completed_xlsx_response(
        request,
        name="Students",
        export_type="students",
        filename=filename,
        sheet_name="Students",
        rows=body,
    )


class AdminManageStudents(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _student_rows()
        filtered_rows = _filter_rows(rows, request.query_params)
        return Response(
            {
                "title": "Manage Students",
                "section": "admin",
                "summary": {
                    "total": len(rows),
                    "active": sum(1 for row in rows if row["is_active"]),
                    "filtered": len(filtered_rows),
                },
                "filters": _filters(rows),
                "students": _public_rows(filtered_rows),
            },
            status=status.HTTP_200_OK,
        )


class AdminManageStudentsExport(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _filter_rows(_student_rows(), request.query_params)
        suffix = (
            "filtered"
            if any(key != "sort" and value for key, value in request.query_params.items())
            else "all"
        )
        return _export_response(request, rows, f"admin-students-{suffix}.xlsx")


class AdminManageStudentDetail(APIView):
    permission_classes = [IsAdminRole]

    def _profile(self, profile_id):
        return (
            models.Profile.objects.select_related(
                "user",
                "student_detail",
                "student_detail__school",
                "student_detail__center",
                "student_detail__program",
            )
            .filter(pk=profile_id, role=models.Profile.ROLE_STUDENT)
            .first()
        )

    def get(self, request, profile_id):
        profile = self._profile(profile_id)
        if not profile:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        row = next(
            (student for student in _student_rows() if student["id"] == profile.id),
            None,
        )
        return Response(
            {
                "title": "Student Detail",
                "section": "admin",
                "student": _public_rows([row])[0] if row else None,
                "options": _student_options(),
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, profile_id):
        profile = self._profile(profile_id)
        if not profile:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        detail, _created = Student.objects.get_or_create(profile=profile)
        profile_updates = []
        detail_updates = []

        if "status" in request.data:
            student_status = str(request.data.get("status") or "").strip().lower()
            if student_status not in STUDENT_STATUS_LABELS:
                return Response(
                    {"detail": "Select a valid student status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            detail.enrollment_status = student_status
            detail_updates.append("enrollment_status")

        if "program_id" in request.data:
            program_id = request.data.get("program_id")
            program = (
                models.Program.objects.select_related("school", "center", "department")
                .filter(pk=program_id, is_active=True)
                .first()
                if program_id
                else None
            )
            if program_id and not program:
                return Response(
                    {"detail": "Program not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            profile.program = program
            profile.school = program.school if program and program.school_id else None
            profile.center = program.center if program and program.center_id else None
            profile.department = (
                program.department if program and program.department_id else None
            )
            profile_updates.extend(["program", "school", "center", "department"])

        if detail_updates:
            detail.save(update_fields=sorted(set(detail_updates)) + ["updated_at"])
        if profile_updates:
            profile.save(update_fields=sorted(set(profile_updates)) + ["updated_at"])

        row = next(
            (student for student in _student_rows() if student["id"] == profile.id),
            None,
        )
        return Response(
            {
                "message": "Student details updated successfully.",
                "student": _public_rows([row])[0] if row else None,
            },
            status=status.HTTP_200_OK,
        )


__all__ = [
    "AdminManageStudents",
    "AdminManageStudentsExport",
    "AdminManageStudentDetail",
]
