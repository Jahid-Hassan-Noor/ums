from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsExecutiveRole
from admin_app.report_exports import completed_xlsx_response
from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    offerings_for_scope,
    scope_payload,
)
from executive_app.evaluation_service import (
    ensure_starter_template,
    export_rows,
    normalize_questions,
    serialize_survey,
    serialize_survey_detail,
    serialize_template,
    surveys_for_scope,
    templates_for_profile,
)
from executive_app.models import CourseEvaluationSurvey, EvaluationTemplate


def _profile_scope_or_response(request):
    profile = get_executive_profile(request.user)
    try:
        scope = get_executive_scope(profile)
    except ValueError as exc:
        return None, None, Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if not profile or not scope.get("kind") or not scope.get("unit"):
        return None, None, Response(
            {"detail": "Executive must be assigned to one school or centre."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return profile, scope, None


def _parse_datetime(value, label):
    if value in (None, ""):
        return None
    parsed = parse_datetime(str(value))
    if not parsed:
        raise ValueError(f"{label} must be a valid date and time.")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _boolean(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _validation_message(exc):
    if hasattr(exc, "message_dict"):
        return " ".join(
            message
            for messages in exc.message_dict.values()
            for message in messages
        )
    return " ".join(exc.messages)


def _offering_payload(offering):
    return {
        "id": offering.id,
        "course": {
            "id": offering.course_id,
            "code": offering.course.code,
            "title": offering.course.title,
        },
        "semester": {
            "id": offering.semester_id,
            "name": offering.semester.name,
            "academic_session": offering.semester.academic_session,
        },
        "section": offering.section,
        "instructor": (
            {
                "id": offering.instructor_id,
                "name": (
                    f"{offering.instructor.user.first_name} {offering.instructor.user.last_name}".strip()
                    or offering.instructor.user.username
                ),
            }
            if offering.instructor_id
            else None
        ),
        "has_survey": hasattr(offering, "course_evaluation"),
    }


class ExecutiveEvaluationTemplates(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        ensure_starter_template(profile)
        return Response(
            {
                "scope": scope_payload(scope),
                "templates": [
                    serialize_template(template)
                    for template in templates_for_profile(profile)
                ],
            }
        )

    def post(self, request):
        profile, _scope, error = _profile_scope_or_response(request)
        if error:
            return error
        try:
            questions = normalize_questions(request.data.get("questions"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        name = str(request.data.get("name") or "").strip()
        if not name:
            return Response(
                {"detail": "Template name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        template = EvaluationTemplate.objects.create(
            name=name,
            description=str(request.data.get("description") or "").strip(),
            questions=questions,
            created_by=profile,
        )
        return Response(
            {
                "message": "Evaluation template created successfully.",
                "template": serialize_template(template),
            },
            status=status.HTTP_201_CREATED,
        )


class ExecutiveEvaluationTemplateDetail(APIView):
    permission_classes = [IsExecutiveRole]

    def _template(self, profile, pk):
        return EvaluationTemplate.objects.filter(
            pk=pk,
            created_by=profile,
            is_active=True,
        ).first()

    def patch(self, request, pk):
        profile, _scope, error = _profile_scope_or_response(request)
        if error:
            return error
        template = self._template(profile, pk)
        if not template:
            return Response({"detail": "Template not found."}, status=status.HTTP_404_NOT_FOUND)

        if "name" in request.data:
            name = str(request.data.get("name") or "").strip()
            if not name:
                return Response(
                    {"detail": "Template name is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            template.name = name
        if "description" in request.data:
            template.description = str(request.data.get("description") or "").strip()
        if "questions" in request.data:
            try:
                template.questions = normalize_questions(request.data.get("questions"))
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        template.save()
        return Response(
            {
                "message": "Evaluation template updated successfully.",
                "template": serialize_template(template),
            }
        )

    def delete(self, request, pk):
        profile, _scope, error = _profile_scope_or_response(request)
        if error:
            return error
        template = self._template(profile, pk)
        if not template:
            return Response({"detail": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        template.is_active = False
        template.save(update_fields=["is_active", "updated_at"])
        return Response({"message": "Evaluation template archived successfully."})


class ExecutiveEvaluationSurveys(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request):
        profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        ensure_starter_template(profile)
        offerings = offerings_for_scope(scope).select_related(
            "course",
            "semester",
            "instructor",
            "instructor__user",
        )
        return Response(
            {
                "title": "SEC-SET Course Evaluations",
                "scope": scope_payload(scope),
                "offerings": [_offering_payload(offering) for offering in offerings],
                "surveys": [
                    serialize_survey(survey)
                    for survey in surveys_for_scope(scope)
                ],
            }
        )

    def post(self, request):
        profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        offering = offerings_for_scope(scope).filter(pk=request.data.get("offering_id")).first()
        if not offering:
            return Response(
                {"detail": "Course offering not found in your executive scope."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if CourseEvaluationSurvey.objects.filter(offering=offering).exists():
            return Response(
                {"detail": "This course offering already has an evaluation survey."},
                status=status.HTTP_409_CONFLICT,
            )

        template = None
        template_id = request.data.get("template_id")
        if template_id:
            template = templates_for_profile(profile).filter(pk=template_id).first()
            if not template:
                return Response({"detail": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            template = ensure_starter_template(profile)

        try:
            questions = normalize_questions(
                request.data.get("questions")
                if "questions" in request.data
                else template.questions
            )
            opens_at = _parse_datetime(request.data.get("opens_at"), "Opening time")
            closes_at = _parse_datetime(request.data.get("closes_at"), "Closing time")
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        survey = CourseEvaluationSurvey(
            offering=offering,
            template=template,
            title=(
                str(request.data.get("title") or "").strip()
                or f"SEC-SET: {offering.course.code} {offering.course.title}"
            ),
            instructions=str(request.data.get("instructions") or "").strip(),
            questions=questions,
            opens_at=opens_at,
            closes_at=closes_at,
            is_published=_boolean(request.data.get("is_published"), default=True),
            is_required=_boolean(request.data.get("is_required"), default=True),
            created_by=profile,
        )
        try:
            survey.full_clean()
            survey.save()
        except ValidationError as exc:
            return Response(
                {"detail": _validation_message(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Course evaluation launched successfully.",
                "survey": serialize_survey(survey, include_questions=True),
            },
            status=status.HTTP_201_CREATED,
        )


class ExecutiveEvaluationSurveyDetail(APIView):
    permission_classes = [IsExecutiveRole]

    def _survey(self, scope, pk):
        return surveys_for_scope(scope).filter(pk=pk).first()

    def get(self, request, pk):
        _profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        survey = self._survey(scope, pk)
        if not survey:
            return Response({"detail": "Evaluation survey not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_survey_detail(survey))

    def patch(self, request, pk):
        _profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        survey = self._survey(scope, pk)
        if not survey:
            return Response({"detail": "Evaluation survey not found."}, status=status.HTTP_404_NOT_FOUND)

        if "questions" in request.data:
            if survey.responses.exists():
                return Response(
                    {"detail": "Questions cannot be changed after students have submitted responses."},
                    status=status.HTTP_409_CONFLICT,
                )
            try:
                survey.questions = normalize_questions(request.data.get("questions"))
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if "title" in request.data:
            title = str(request.data.get("title") or "").strip()
            if not title:
                return Response({"detail": "Survey title is required."}, status=status.HTTP_400_BAD_REQUEST)
            survey.title = title
        if "instructions" in request.data:
            survey.instructions = str(request.data.get("instructions") or "").strip()
        try:
            if "opens_at" in request.data:
                survey.opens_at = _parse_datetime(request.data.get("opens_at"), "Opening time")
            if "closes_at" in request.data:
                survey.closes_at = _parse_datetime(request.data.get("closes_at"), "Closing time")
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if "is_published" in request.data:
            survey.is_published = _boolean(request.data.get("is_published"))
        if "is_required" in request.data:
            survey.is_required = _boolean(request.data.get("is_required"))
        try:
            survey.full_clean()
            survey.save()
        except ValidationError as exc:
            return Response(
                {"detail": _validation_message(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Evaluation survey updated successfully.",
                "survey": serialize_survey_detail(survey),
            }
        )

    def delete(self, request, pk):
        _profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        survey = self._survey(scope, pk)
        if not survey:
            return Response({"detail": "Evaluation survey not found."}, status=status.HTTP_404_NOT_FOUND)
        if survey.responses.exists():
            return Response(
                {"detail": "A survey with submitted responses cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        survey.delete()
        return Response({"message": "Evaluation survey deleted successfully."})


class ExecutiveEvaluationSurveyExport(APIView):
    permission_classes = [IsExecutiveRole]

    def get(self, request, pk):
        _profile, scope, error = _profile_scope_or_response(request)
        if error:
            return error
        survey = surveys_for_scope(scope).filter(pk=pk).first()
        if not survey:
            return Response({"detail": "Evaluation survey not found."}, status=status.HTTP_404_NOT_FOUND)
        safe_code = survey.offering.course.code.lower().replace(" ", "-")
        return completed_xlsx_response(
            request,
            name=f"SEC-SET {survey.offering.course.code}",
            export_type="course-evaluation",
            filename=f"sec-set-{safe_code}-{survey.offering.semester_id}.xlsx",
            sheet_name="SEC-SET",
            rows=export_rows(survey),
            metadata={
                "scope": scope_payload(scope),
                "survey_id": survey.id,
                "offering_id": survey.offering_id,
            },
        )


__all__ = [
    "ExecutiveEvaluationTemplates",
    "ExecutiveEvaluationTemplateDetail",
    "ExecutiveEvaluationSurveys",
    "ExecutiveEvaluationSurveyDetail",
    "ExecutiveEvaluationSurveyExport",
]
