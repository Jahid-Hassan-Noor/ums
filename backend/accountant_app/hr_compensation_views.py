from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsAccountantRole
from hr_app.models import CompensationChangeRequest
from hr_app.service import (
    compensation_request_payload,
    compensation_requests_payload,
    review_compensation_request,
)


def validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(error, "messages"):
        return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class AccountantCompensationRequests(APIView):
    permission_classes = [IsAccountantRole]

    def get(self, request):
        status_value = request.query_params.get("status")
        if status_value and status_value not in dict(CompensationChangeRequest.STATUS_CHOICES):
            return Response({"detail": "Unsupported compensation request status."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(compensation_requests_payload(status_value=status_value))

    def patch(self, request):
        try:
            request_obj = review_compensation_request(
                actor=request.user.profile,
                request_id=request.data.get("request_id"),
                status_value=request.data.get("status"),
                review_note=request.data.get("review_note"),
            )
        except ValidationError as error:
            return validation_response(error)
        return Response(
            {
                "message": f"Compensation request {request_obj.get_status_display().lower()}.",
                "request": compensation_request_payload(request_obj),
            }
        )


__all__ = ["AccountantCompensationRequests"]
