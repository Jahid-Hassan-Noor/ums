from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsExecutiveRole
from admin_app.report_exports import completed_xlsx_response
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    scope_payload,
)
from executive_app.reporting import (
    filter_result_rows,
    filter_student_rows,
    filter_teacher_rows,
    result_filters,
    result_rows,
    results_workbook,
    student_filters,
    student_rows,
    students_workbook,
    teacher_filters,
    teacher_rows,
    teachers_workbook,
)


def _scope_or_response(request):
    profile = get_executive_profile(request.user)
    try:
        scope = get_executive_scope(profile)
    except ValueError as exc:
        return None, Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if not scope.get("kind") or not scope.get("unit"):
        return None, Response(
            {"detail": "Executive must be assigned to one school or centre."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return scope, None


def _metadata(scope):
    return {"scope": scope_payload(scope)}


class ExecutiveReports(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        scope, error = _scope_or_response(request)
        if error:
            return error
        students = student_rows(scope)
        teachers = teacher_rows(scope)
        results = result_rows(scope)
        return Response(
            {
                "title": "Reports",
                "section": "executive",
                "scope": scope_payload(scope),
                "students": {
                    "count": len(students),
                    "filters": student_filters(students),
                },
                "teachers": {
                    "count": len(teachers),
                    "filters": teacher_filters(teachers),
                },
                "results": {
                    "count": len(results),
                    "filters": result_filters(results),
                },
            }
        )


class ExecutiveStudentsReportExport(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        scope, error = _scope_or_response(request)
        if error:
            return error
        rows = filter_student_rows(student_rows(scope), request.query_params)
        return completed_xlsx_response(
            request,
            name=f"{scope['unit'].code} Students",
            export_type="executive-students",
            filename=f"{scope['unit'].code.lower()}-students.xlsx",
            sheet_name="Students",
            rows=students_workbook(rows),
            metadata=_metadata(scope),
        )


class ExecutiveTeachersReportExport(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        scope, error = _scope_or_response(request)
        if error:
            return error
        rows = filter_teacher_rows(teacher_rows(scope), request.query_params)
        return completed_xlsx_response(
            request,
            name=f"{scope['unit'].code} Teachers",
            export_type="executive-teachers",
            filename=f"{scope['unit'].code.lower()}-teachers.xlsx",
            sheet_name="Teachers",
            rows=teachers_workbook(rows),
            metadata=_metadata(scope),
        )


class ExecutiveFinalResultsReportExport(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        scope, error = _scope_or_response(request)
        if error:
            return error
        rows = filter_result_rows(result_rows(scope), request.query_params)
        return completed_xlsx_response(
            request,
            name=f"{scope['unit'].code} Final Results",
            export_type="executive-final-results",
            filename=f"{scope['unit'].code.lower()}-final-results.xlsx",
            sheet_name="Final Results",
            rows=results_workbook(rows),
            metadata=_metadata(scope),
        )


__all__ = [
    "ExecutiveReports",
    "ExecutiveStudentsReportExport",
    "ExecutiveTeachersReportExport",
    "ExecutiveFinalResultsReportExport",
]
