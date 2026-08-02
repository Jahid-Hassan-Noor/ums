from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.report_exports import completed_xlsx_response
from teacher_app.models import Teacher, TeacherScopeAssignment


def _display_name(profile):
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _detail_for(profile):
    try:
        return profile.teacher_detail
    except Teacher.DoesNotExist:
        return None


def _option(value, label):
    return {"value": str(value), "label": str(label)}


def _staff_options(rows=None):
    designations = sorted(
        {row["designation"] for row in rows or [] if row["designation"]}
    )
    return {
        "schools": [
            _option(school.id, f"{school.code} - {school.name}")
            for school in models.School.objects.filter(is_active=True).order_by("name")
        ],
        "centers": [
            _option(center.id, f"{center.code} - {center.name}")
            for center in models.Center.objects.filter(is_active=True).order_by("name")
        ],
        "units": [
            {
                "value": str(unit.id),
                "label": f"{unit.code} - {unit.name}",
                "school": unit.school_id,
                "center": unit.center_id,
                "department": unit.department_id,
            }
            for unit in models.Unit.objects.filter(is_active=True).order_by("name")
        ],
        "departments": [
            {
                "value": str(department.id),
                "label": f"{department.code} - {department.name}",
                "school": department.school_id,
                "center": department.center_id,
            }
            for department in models.Department.objects.filter(is_active=True).order_by("name")
        ],
        "designations": [_option(designation, designation) for designation in designations],
    }


def _teacher_rows():
    profiles = (
        models.Profile.objects.select_related(
            "user",
            "teacher_detail",
            "teacher_detail__school",
            "teacher_detail__center",
            "teacher_detail__unit",
            "teacher_detail__unit__department",
            "teacher_detail__department",
        )
        .prefetch_related(
            "teacher_scope_assignments__school",
            "teacher_scope_assignments__center",
        )
        .filter(role=models.Profile.ROLE_TEACHER)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    rows = []
    for profile in profiles:
        detail = _detail_for(profile)
        department = profile.department or (
            profile.unit.department if profile.unit_id and profile.unit.department_id else None
        )
        designation = profile.designation or (detail.designation if detail else "")
        staff_id = profile.staff_id or (detail.staff_id if detail else "")
        assignments = [
            {
                "id": assignment.id,
                "school": assignment.school_id,
                "school_code": assignment.school.code if assignment.school_id else "",
                "school_name": assignment.school.name if assignment.school_id else "",
                "center": assignment.center_id,
                "center_code": assignment.center.code if assignment.center_id else "",
                "center_name": assignment.center.name if assignment.center_id else "",
                "is_primary": assignment.is_primary,
            }
            for assignment in profile.teacher_scope_assignments.all()
            if assignment.is_active
        ]
        row = {
            "id": profile.id,
            "user_id": profile.user_id,
            "username": profile.user.username,
            "name": _display_name(profile),
            "email": profile.user.email,
            "staff_id": staff_id,
            "designation": designation,
            "phone": profile.phone,
            "school": profile.school_id,
            "school_code": profile.school.code if profile.school_id else "",
            "school_name": profile.school.name if profile.school_id else "",
            "center": profile.center_id,
            "center_code": profile.center.code if profile.center_id else "",
            "center_name": profile.center.name if profile.center_id else "",
            "unit": profile.unit_id,
            "unit_code": profile.unit.code if profile.unit_id else "",
            "unit_name": profile.unit.name if profile.unit_id else "",
            "department": department.id if department else None,
            "department_code": department.code if department else "",
            "department_name": department.name if department else "",
            "academic_rank": detail.academic_rank if detail else "",
            "specialization": detail.specialization if detail else "",
            "office_location": detail.office_location if detail else "",
            "assignments": assignments,
            "is_active": bool(profile.is_active and profile.user.is_active),
        }
        row["search_text"] = " ".join(
            str(value or "")
            for value in [
                row["name"],
                row["username"],
                row["email"],
                row["staff_id"],
                row["designation"],
                row["school_name"],
                row["school_code"],
                row["center_name"],
                row["center_code"],
                row["unit_name"],
                row["unit_code"],
                row["department_name"],
                row["department_code"],
                row["academic_rank"],
                row["specialization"],
                *[
                    assignment["school_name"]
                    or assignment["school_code"]
                    or assignment["center_name"]
                    or assignment["center_code"]
                    for assignment in assignments
                ],
            ]
        ).lower()
        rows.append(row)
    return rows


def _filter_rows(rows, params):
    query = str(params.get("q", "")).strip().lower()
    school = str(params.get("school", "")).strip()
    center = str(params.get("center", "")).strip()
    unit = str(params.get("unit", "")).strip()
    department = str(params.get("department", "")).strip()
    designation = str(params.get("designation", "")).strip()

    filtered = []
    for row in rows:
        if query and query not in row["search_text"]:
            continue
        if school and not any(
            str(assignment["school"] or "") == school
            for assignment in row["assignments"]
        ):
            continue
        if center and not any(
            str(assignment["center"] or "") == center
            for assignment in row["assignments"]
        ):
            continue
        if unit and str(row["unit"] or "") != unit:
            continue
        if department and str(row["department"] or "") != department:
            continue
        if designation and row["designation"] != designation:
            continue
        filtered.append(row)

    reverse = str(params.get("sort", "asc")).strip().lower() == "desc"
    filtered.sort(
        key=lambda row: (
            str(row["name"] or "").lower(),
            str(row["staff_id"] or "").lower(),
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
    return _staff_options(rows)


def _resolve_assignment(data):
    school_id = data.get("school_id")
    center_id = data.get("center_id")
    unit_id = data.get("unit_id")
    department_id = data.get("department_id")

    school = models.School.objects.filter(pk=school_id).first() if school_id else None
    center = models.Center.objects.filter(pk=center_id).first() if center_id else None
    unit = models.Unit.objects.filter(pk=unit_id).first() if unit_id else None
    department = (
        models.Department.objects.filter(pk=department_id).first()
        if department_id
        else None
    )

    if unit:
        if not school and unit.school_id:
            school = unit.school
        if not center and unit.center_id:
            center = unit.center
        if not department and unit.department_id:
            department = unit.department

    if department:
        if not school and department.school_id:
            school = department.school
        if not center and department.center_id:
            center = department.center

    if bool(school) == bool(center):
        return None, None, None, None, "Assign exactly one school or centre."
    if unit and school and unit.school_id and unit.school_id != school.id:
        return None, None, None, None, "Selected unit does not belong to the selected school."
    if unit and center and unit.center_id and unit.center_id != center.id:
        return None, None, None, None, "Selected unit does not belong to the selected centre."
    if department and school and department.school_id and department.school_id != school.id:
        return None, None, None, None, "Selected department does not belong to the selected school."
    if department and center and department.center_id and department.center_id != center.id:
        return None, None, None, None, "Selected department does not belong to the selected centre."

    return school, center, unit, department, None


def _export_response(request, rows, filename):
    headers = [
        "Staff ID",
        "Name",
        "Username",
        "Email",
        "Phone",
        "Designation",
        "Academic Rank",
        "Specialization",
        "School",
        "Centre",
        "Unit",
        "Department",
        "Office",
        "Active",
    ]
    body = [headers]
    for row in rows:
        body.append(
            [
                row["staff_id"],
                row["name"],
                row["username"],
                row["email"],
                row["phone"],
                row["designation"],
                row["academic_rank"],
                row["specialization"],
                row["school_name"] or row["school_code"],
                row["center_name"] or row["center_code"],
                row["unit_name"] or row["unit_code"],
                row["department_name"] or row["department_code"],
                row["office_location"],
                "Yes" if row["is_active"] else "No",
            ]
        )

    return completed_xlsx_response(
        request,
        name="Teachers",
        export_type="teachers",
        filename=filename,
        sheet_name="Teachers",
        rows=body,
    )


class AdminManageTeachers(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _teacher_rows()
        filtered_rows = _filter_rows(rows, request.query_params)
        return Response(
            {
                "title": "Manage Teachers",
                "section": "admin",
                "summary": {
                    "total": len(rows),
                    "active": sum(1 for row in rows if row["is_active"]),
                    "filtered": len(filtered_rows),
                },
                "filters": _filters(rows),
                "teachers": _public_rows(filtered_rows),
            },
            status=status.HTTP_200_OK,
        )


class AdminManageTeachersExport(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _filter_rows(_teacher_rows(), request.query_params)
        suffix = (
            "filtered"
            if any(key != "sort" and value for key, value in request.query_params.items())
            else "all"
        )
        return _export_response(request, rows, f"admin-teachers-{suffix}.xlsx")


class AdminManageTeacherDetail(APIView):
    permission_classes = [IsAdminRole]

    def _profile(self, profile_id):
        return (
            models.Profile.objects.select_related(
                "user",
                "teacher_detail",
                "teacher_detail__school",
                "teacher_detail__center",
                "teacher_detail__unit",
                "teacher_detail__unit__department",
                "teacher_detail__department",
            )
            .filter(pk=profile_id, role=models.Profile.ROLE_TEACHER)
            .first()
        )

    def get(self, request, profile_id):
        profile = self._profile(profile_id)
        if not profile:
            return Response(
                {"detail": "Teacher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        rows = _teacher_rows()
        row = next((teacher for teacher in rows if teacher["id"] == profile.id), None)
        return Response(
            {
                "title": "Teacher Detail",
                "section": "admin",
                "teacher": _public_rows([row])[0] if row else None,
                "options": _staff_options(rows),
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, profile_id):
        profile = self._profile(profile_id)
        if not profile:
            return Response(
                {"detail": "Teacher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        detail, _created = Teacher.objects.get_or_create(profile=profile)
        profile_updates = []
        detail_updates = []

        if "designation" in request.data:
            designation = str(request.data.get("designation") or "").strip()
            profile.designation = designation
            detail.designation = designation
            profile_updates.append("designation")
            detail_updates.append("designation")

        assignment_fields = {"school_id", "center_id", "unit_id", "department_id"}
        if assignment_fields.intersection(request.data.keys()):
            school, center, unit, department, error = _resolve_assignment(request.data)
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
            profile.school = school
            profile.center = center
            profile.unit = unit
            profile.department = department
            profile_updates.extend(["school", "center", "unit", "department"])
            TeacherScopeAssignment.objects.filter(
                teacher=profile,
                is_primary=True,
            ).update(is_primary=False)
            assignment, _created = TeacherScopeAssignment.objects.get_or_create(
                teacher=profile,
                school=school,
                center=center,
            )
            assignment.is_primary = True
            assignment.is_active = True
            assignment.save(update_fields=["is_primary", "is_active", "updated_at"])

        if profile_updates:
            profile.save(update_fields=sorted(set(profile_updates)) + ["updated_at"])
        if detail_updates:
            detail.save(update_fields=sorted(set(detail_updates)) + ["updated_at"])

        rows = _teacher_rows()
        row = next((teacher for teacher in rows if teacher["id"] == profile.id), None)
        return Response(
            {
                "message": "Teacher details updated successfully.",
                "teacher": _public_rows([row])[0] if row else None,
            },
            status=status.HTTP_200_OK,
        )


__all__ = [
    "AdminManageTeachers",
    "AdminManageTeachersExport",
    "AdminManageTeacherDetail",
]
