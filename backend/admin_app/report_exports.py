from pathlib import Path

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.utils import timezone

from admin_app import models
from admin_app.xlsx import build_xlsx
from notifications_package.service import notify_profile


XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _report_url(profile):
    if profile and profile.role == models.Profile.ROLE_EXECUTIVE:
        return "/executive/reports"
    return "/admin/reports/exports"


def _notify_report(report):
    if not report.requested_by:
        return
    notify_profile(
        report.requested_by,
        actor=None,
        event_type=f"reports.{report.status}",
        verb=f"Report export {report.name} {report.status}.",
        data={
            "report_export_id": report.id,
            "export_type": report.export_type,
            "status": report.status,
            "error_message": report.error_message,
        },
        url=_report_url(report.requested_by),
    )


def _request_filters(request):
    return {
        key: request.query_params.get(key)
        for key in request.query_params
        if request.query_params.get(key) not in (None, "")
    }


def _audit(request, action, report):
    details = {
        "name": report.name,
        "export_type": report.export_type,
        "status": report.status,
        "filters": report.filters or {},
    }
    if (report.filters or {}).get("scope"):
        details["scope"] = report.filters["scope"]
    models.AuditLog.objects.create(
        user=getattr(request.user, "profile", None),
        action=action,
        object_type="ReportExport",
        object_id=str(report.id),
        details=details,
    )


def completed_xlsx_response(
    request,
    *,
    name,
    export_type,
    filename,
    sheet_name,
    rows,
    metadata=None,
):
    report = models.ReportExport.objects.create(
        name=name,
        export_type=export_type,
        status=models.ReportExport.STATUS_RUNNING,
        requested_by=getattr(request.user, "profile", None),
        filters={
            **_request_filters(request),
            **(metadata or {}),
            "row_count": max(len(rows) - 1, 0),
        },
    )
    try:
        content = build_xlsx(rows, sheet_name=sheet_name)
        report.file.save(Path(filename).name, ContentFile(content), save=False)
        report.status = models.ReportExport.STATUS_COMPLETED
        report.completed_at = timezone.now()
        report.save(
            update_fields=[
                "file",
                "status",
                "completed_at",
            ]
        )
        _audit(request, "report.export.completed", report)
    except Exception as exc:
        report.status = models.ReportExport.STATUS_FAILED
        report.error_message = str(exc)
        report.completed_at = timezone.now()
        report.save(update_fields=["status", "error_message", "completed_at"])
        _audit(request, "report.export.failed", report)
        _notify_report(report)
        raise

    _notify_report(report)
    response = HttpResponse(content, content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{Path(filename).name}"'
    return response
