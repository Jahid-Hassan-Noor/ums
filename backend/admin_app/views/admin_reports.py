from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from auth_app.permissions import IsAdminRole
from admin_app.report_catalog import report_catalog, report_rows
from admin_app.report_exports import completed_xlsx_response


class AdminReports(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "title": "Reports",
                "section": "admin",
                "reports": report_catalog(),
            },
            status=status.HTTP_200_OK,
        )


class AdminReportGenerate(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, report_type):
        try:
            definition, rows = report_rows(report_type, request.query_params)
        except KeyError:
            return Response({"detail": "Unknown report type."}, status=status.HTTP_404_NOT_FOUND)

        return completed_xlsx_response(
            request,
            name=definition["name"],
            export_type=report_type,
            filename=f"{report_type}.xlsx",
            sheet_name=definition["name"],
            rows=rows,
        )
