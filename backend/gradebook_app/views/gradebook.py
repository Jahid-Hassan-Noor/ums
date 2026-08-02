from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsAdminRole, IsStudentRole, IsTeacherRole
from gradebook_app.services import (
    GradebookWorkflowError,
    admin_gradebook_payload,
    save_scale,
    student_gradebook_payload,
    teacher_gradebook_action,
    teacher_gradebook_payload,
)


def workflow_error_response(error):
    return Response({"detail": str(error)}, status=error.status_code)


class AdminGradebook(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(admin_gradebook_payload(), status=status.HTTP_200_OK)

    def post(self, request):
        action = str(request.data.get("action") or "save_scale").strip().lower()
        if action != "save_scale":
            return Response({"detail": "Unsupported gradebook action."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            scale = save_scale(request.user.profile, request.data)
        except GradebookWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Grade scale saved.",
                "scale": scale,
                **admin_gradebook_payload(),
            },
            status=status.HTTP_200_OK,
        )


class TeacherGradebook(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        offering_id = request.query_params.get("offering_id")
        return Response(
            teacher_gradebook_payload(request.user, offering_id=offering_id),
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            message, payload = teacher_gradebook_action(request.user, request.data)
        except GradebookWorkflowError as exc:
            return workflow_error_response(exc)
        return Response({"message": message, **payload}, status=status.HTTP_200_OK)


class StudentGradebook(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(student_gradebook_payload(request.user), status=status.HTTP_200_OK)
