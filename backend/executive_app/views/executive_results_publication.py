from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsExecutiveRole
from executive_app.results_service import (
    ResultWorkflowError,
    executive_results_payload,
    publish_result_batch,
)


class ExecutiveResultsPublication(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        return Response(
            executive_results_payload(request.user, view="publication"),
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            message, batch = publish_result_batch(request.user, request.data)
        except (ResultWorkflowError, ValueError) as exc:
            return Response(
                {"detail": str(exc)},
                status=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
            )
        return Response(
            {"message": message, "batch": batch},
            status=status.HTTP_200_OK,
        )
