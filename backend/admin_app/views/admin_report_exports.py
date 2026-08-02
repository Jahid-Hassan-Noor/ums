from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole


def _profile_name(profile):
    if not profile:
        return ""
    user = profile.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _export_payload(item):
    return {
        "id": item.id,
        "name": item.name,
        "export_type": item.export_type,
        "status": item.status,
        "requested_by": _profile_name(item.requested_by),
        "filters": item.filters or {},
        "filename": item.file.name.rsplit("/", 1)[-1] if item.file else "",
        "error_message": item.error_message,
        "created_at": item.created_at,
        "completed_at": item.completed_at,
    }


class AdminReportExports(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        exports = models.ReportExport.objects.select_related(
            "requested_by__user"
        ).order_by("-created_at")[:250]
        return Response(
            {
                "title": "Report Exports",
                "section": "admin",
                "summary": {
                    "total": models.ReportExport.objects.count(),
                    "processing": models.ReportExport.objects.filter(
                        status__in=[
                            models.ReportExport.STATUS_PENDING,
                            models.ReportExport.STATUS_RUNNING,
                        ]
                    ).count(),
                    "completed": models.ReportExport.objects.filter(
                        status=models.ReportExport.STATUS_COMPLETED
                    ).count(),
                    "failed": models.ReportExport.objects.filter(
                        status=models.ReportExport.STATUS_FAILED
                    ).count(),
                },
                "exports": [_export_payload(item) for item in exports],
            },
            status=status.HTTP_200_OK,
        )


class AdminReportExportDetail(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, pk):
        report = models.ReportExport.objects.filter(pk=pk).first()
        if not report:
            return Response({"detail": "Export not found."}, status=status.HTTP_404_NOT_FOUND)
        if report.status != models.ReportExport.STATUS_COMPLETED or not report.file:
            return Response(
                {"detail": "This export does not have a completed file."},
                status=status.HTTP_409_CONFLICT,
            )
        return FileResponse(
            report.file.open("rb"),
            as_attachment=True,
            filename=report.file.name.rsplit("/", 1)[-1],
        )

    def delete(self, request, pk):
        report = models.ReportExport.objects.filter(pk=pk).first()
        if not report:
            return Response({"detail": "Export not found."}, status=status.HTTP_404_NOT_FOUND)
        models.AuditLog.objects.create(
            user=getattr(request.user, "profile", None),
            action="report.export.deleted",
            object_type="ReportExport",
            object_id=str(report.id),
            details={
                "name": report.name,
                "export_type": report.export_type,
                "status": report.status,
            },
        )
        report.delete()
        return Response({"message": "Export deleted."}, status=status.HTTP_200_OK)
