from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsTeacherRole
from executive_app.results_service import (
    ResultWorkflowError,
    save_teacher_results,
    teacher_results_payload,
)


class TeacherResultsSubmit(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        return Response(
            teacher_results_payload(
                request.user,
                view="submit",
                offering_id=request.query_params.get("offering_id"),
            ),
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            message, batch = save_teacher_results(request.user, request.data)
        except ResultWorkflowError as exc:
            return Response(
                {"detail": str(exc)},
                status=exc.status_code,
            )
        return Response(
            {"message": message, "batch": batch},
            status=status.HTTP_200_OK,
        )
