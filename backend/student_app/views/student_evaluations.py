from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from core.common.academic_policy import evaluation_activity_label
from executive_app.evaluation_service import (
    serialize_student_survey,
    student_surveys,
    survey_is_open,
    validate_answers,
)
from executive_app.models import CourseEvaluationResponse, CourseEvaluationSurvey
from student_app.models import Enrollment
from student_app.registration_service import get_student_profile


def _eligible_survey(student, pk):
    return (
        CourseEvaluationSurvey.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "offering__instructor",
            "offering__instructor__user",
            "template",
        )
        .filter(
            pk=pk,
            is_published=True,
            offering__enrollment__student=student,
        )
        .distinct()
        .first()
    )


class StudentEvaluations(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        surveys = list(student_surveys(student))
        serialized = [
            serialize_student_survey(survey, student)
            for survey in surveys
        ]
        return Response(
            {
                "title": f"Student {evaluation_activity_label()}s",
                "evaluation_label": evaluation_activity_label(),
                "summary": {
                    "total": len(serialized),
                    "pending": sum(1 for survey in serialized if not survey["submitted"]),
                    "submitted": sum(1 for survey in serialized if survey["submitted"]),
                },
                "surveys": serialized,
            }
        )


class StudentEvaluationDetail(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request, pk):
        student = get_student_profile(request.user)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        survey = _eligible_survey(student, pk)
        if not survey:
            return Response({"detail": "Evaluation survey not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_student_survey(survey, student, include_questions=True))

    def post(self, request, pk):
        student = get_student_profile(request.user)
        if not student:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        survey = _eligible_survey(student, pk)
        if not survey:
            return Response({"detail": "Evaluation survey not found."}, status=status.HTTP_404_NOT_FOUND)
        if not Enrollment.objects.filter(student=student, offering=survey.offering).exists():
            return Response(
                {"detail": "Only students enrolled in this course may submit the evaluation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if survey.responses.filter(student=student).exists():
            return Response(
                {"detail": "You have already submitted this course evaluation."},
                status=status.HTTP_409_CONFLICT,
            )
        if not survey_is_open(survey):
            return Response(
                {"detail": "This course evaluation is not currently open for submissions."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            answers = validate_answers(survey, request.data.get("answers"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = CourseEvaluationResponse.objects.create(
                survey=survey,
                student=student,
                answers=answers,
            )
        except IntegrityError:
            return Response(
                {"detail": "You have already submitted this course evaluation."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                "message": f"Thank you. Your {evaluation_activity_label().lower()} has been submitted.",
                "submitted_at": response.submitted_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


__all__ = ["StudentEvaluations", "StudentEvaluationDetail"]
