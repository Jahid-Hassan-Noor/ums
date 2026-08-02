from copy import deepcopy

from django.db.models import Q
from django.utils import timezone

from executive_app.course_schedule import offerings_for_scope, profile_display_name
from executive_app.models import (
    CourseEvaluationResponse,
    CourseEvaluationSurvey,
    EvaluationTemplate,
)
from student_app.models import Enrollment


LIKERT_OPTIONS = [
    {"value": "strongly_agree", "label": "Strongly Agree", "score": 4},
    {"value": "agree", "label": "Agree", "score": 3},
    {"value": "disagree", "label": "Disagree", "score": 2},
    {"value": "strongly_disagree", "label": "Strongly Disagree", "score": 1},
]
LIKERT_VALUES = {option["value"] for option in LIKERT_OPTIONS}
LIKERT_LABELS = {option["value"]: option["label"] for option in LIKERT_OPTIONS}
LIKERT_SCORES = {option["value"]: option["score"] for option in LIKERT_OPTIONS}


DEFAULT_QUESTIONS = [
    {
        "id": "content_objectives_clear",
        "section": "Course Content",
        "text": "The learning objectives of the course are clearly stated and understandable.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_outcomes_covered",
        "section": "Course Content",
        "text": "The course content covers all the learning outcomes.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_organized",
        "section": "Course Content",
        "text": "The course is organized in a coherent and sequential manner.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_knowledge",
        "section": "Course Content",
        "text": "This course content has increased my knowledge.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_skills",
        "section": "Course Content",
        "text": "This course content has increased my skills.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_learning_needs",
        "section": "Course Content",
        "text": "This course meets my learning needs at this time.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_materials_relevant",
        "section": "Course Content",
        "text": "The materials provided are relevant to the course content.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_materials_helpful",
        "section": "Course Content",
        "text": "The materials provided helped to increase my learning.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_assessment_alignment",
        "section": "Course Content",
        "text": "The type and quality of assessments are appropriate and aligned to learning objectives.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_class_workload",
        "section": "Course Content",
        "text": "The workload during class is reasonable in this course.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_homework_manageable",
        "section": "Course Content",
        "text": "The homework outside of class is manageable in this course.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "content_general_comments",
        "section": "Course Content",
        "text": "Please write any general comments about the course.",
        "type": "text",
        "required": True,
    },
    {
        "id": "teaching_study_guide",
        "section": "Teaching Effectiveness",
        "text": "My lecturer provides course-related information through a study guide.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_materials_advance",
        "section": "Teaching Effectiveness",
        "text": "My lecturer posts course materials in the learning management system in advance.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_participation",
        "section": "Teaching Effectiveness",
        "text": "My lecturer encourages students to actively participate in the session by sharing ideas.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_collaborative",
        "section": "Teaching Effectiveness",
        "text": "My lecturer facilitates learning through interactive and collaborative activities.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_self_directed",
        "section": "Teaching Effectiveness",
        "text": "My lecturer promotes self-directed learning, guided discovery, and reflection.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_technology",
        "section": "Teaching Effectiveness",
        "text": "My lecturer uses various technology tools to facilitate communication and learning.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_innovation",
        "section": "Teaching Effectiveness",
        "text": "My lecturer applies new teaching methods that innovatively enhance student learning.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "teaching_attendance",
        "section": "Teaching Effectiveness",
        "text": "My lecturer records and communicates students' attendance throughout the semester.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "assessment_instructions",
        "section": "Assessment",
        "text": "My lecturer gives clear assessment instructions, including rubrics.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "assessment_questions",
        "section": "Assessment",
        "text": "My lecturer provides a platform for students to ask questions about assessments.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "assessment_timing",
        "section": "Assessment",
        "text": "My lecturer conducts coursework or continuous assessments before the end of the semester.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "assessment_progress_feedback",
        "section": "Assessment",
        "text": "My lecturer provides constructive feedback while the work is in progress.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "assessment_grade_feedback",
        "section": "Assessment",
        "text": "My lecturer gives feedback on students' achievements or grades within a reasonable period.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_prepared",
        "section": "General Conduct",
        "text": "My lecturer comes to class well-prepared.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_fair",
        "section": "General Conduct",
        "text": "My lecturer is fair in dealing with students.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_on_time",
        "section": "General Conduct",
        "text": "My lecturer comes to class on time.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_listens",
        "section": "General Conduct",
        "text": "My lecturer listens to my ideas and opinions.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_clear_speech",
        "section": "General Conduct",
        "text": "My lecturer speaks clearly.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_respect",
        "section": "General Conduct",
        "text": "My lecturer shows respect for all students.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "conduct_class_management",
        "section": "General Conduct",
        "text": "My lecturer manages our class well.",
        "type": "likert",
        "required": True,
    },
    {
        "id": "lecturer_best",
        "section": "Comments About My Lecturer",
        "text": "The best things about my lecturer are:",
        "type": "text",
        "required": True,
    },
    {
        "id": "lecturer_improve",
        "section": "Comments About My Lecturer",
        "text": "My lecturer could improve by:",
        "type": "text",
        "required": True,
    },
]


def default_questions():
    return deepcopy(DEFAULT_QUESTIONS)


def normalize_questions(raw_questions):
    if not isinstance(raw_questions, list) or not raw_questions:
        raise ValueError("Add at least one evaluation question.")

    normalized = []
    seen_ids = set()
    for index, raw in enumerate(raw_questions, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Question {index} is invalid.")
        question_id = str(raw.get("id") or f"question_{index}").strip()
        text = str(raw.get("text") or "").strip()
        section = str(raw.get("section") or "General").strip()
        question_type = str(raw.get("type") or "likert").strip().lower()
        if not question_id or question_id in seen_ids:
            raise ValueError(f"Question {index} needs a unique identifier.")
        if not text:
            raise ValueError(f"Question {index} needs question text.")
        if question_type not in {"likert", "text"}:
            raise ValueError(f"Question {index} must be a Likert or text question.")
        seen_ids.add(question_id)
        normalized.append(
            {
                "id": question_id,
                "section": section or "General",
                "text": text,
                "type": question_type,
                "required": bool(raw.get("required", True)),
            }
        )
    return normalized


def ensure_starter_template(profile):
    template = (
        EvaluationTemplate.objects.filter(created_by=profile, is_active=True)
        .order_by("id")
        .first()
    )
    if template:
        return template
    return EvaluationTemplate.objects.create(
        name="AIU SEC-SET Standard Template",
        description=(
            "Standard course-content and teaching evaluation based on the university's "
            "existing SEC-SET Google Form."
        ),
        questions=default_questions(),
        created_by=profile,
    )


def templates_for_profile(profile):
    return EvaluationTemplate.objects.filter(created_by=profile, is_active=True).order_by("name", "id")


def serialize_template(template):
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "questions": template.questions,
        "question_count": len(template.questions or []),
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


def surveys_for_scope(scope):
    return (
        CourseEvaluationSurvey.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "offering__instructor",
            "offering__instructor__user",
            "template",
            "created_by",
        )
        .filter(offering__in=offerings_for_scope(scope))
        .order_by("-created_at")
    )


def eligible_enrollments(survey):
    return (
        Enrollment.objects.select_related("student", "student__user", "student__student_detail")
        .filter(offering=survey.offering)
        .order_by(
            "student__user__first_name",
            "student__user__last_name",
            "student__user__username",
        )
    )


def survey_state(survey, now=None):
    now = now or timezone.now()
    if not survey.is_published:
        return "draft"
    if survey.opens_at and now < survey.opens_at:
        return "upcoming"
    if survey.closes_at and now > survey.closes_at:
        return "closed"
    return "open"


def survey_is_open(survey, now=None):
    return survey_state(survey, now=now) == "open"


def serialize_survey(survey, include_questions=False):
    eligible_count = eligible_enrollments(survey).count()
    response_count = survey.responses.count()
    offering = survey.offering
    instructor = offering.instructor
    payload = {
        "id": survey.id,
        "title": survey.title,
        "instructions": survey.instructions,
        "offering": {
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
                {"id": instructor.id, "name": profile_display_name(instructor)}
                if instructor
                else None
            ),
        },
        "template": (
            {"id": survey.template_id, "name": survey.template.name}
            if survey.template_id
            else None
        ),
        "opens_at": survey.opens_at.isoformat() if survey.opens_at else None,
        "closes_at": survey.closes_at.isoformat() if survey.closes_at else None,
        "is_published": survey.is_published,
        "is_required": survey.is_required,
        "state": survey_state(survey),
        "eligible_count": eligible_count,
        "response_count": response_count,
        "pending_count": max(eligible_count - response_count, 0),
        "completion_rate": round((response_count / eligible_count) * 100, 1)
        if eligible_count
        else 0,
        "created_at": survey.created_at.isoformat(),
        "updated_at": survey.updated_at.isoformat(),
    }
    if include_questions:
        payload["questions"] = survey.questions
        payload["likert_options"] = LIKERT_OPTIONS
    return payload


def response_analytics(survey):
    responses = list(survey.responses.select_related("student", "student__user"))
    analytics = []
    for question in survey.questions or []:
        question_id = question["id"]
        if question["type"] == "likert":
            counts = {value: 0 for value in LIKERT_VALUES}
            score_total = 0
            answered = 0
            for response in responses:
                value = response.answers.get(question_id)
                if value not in LIKERT_VALUES:
                    continue
                counts[value] += 1
                score_total += LIKERT_SCORES[value]
                answered += 1
            analytics.append(
                {
                    "id": question_id,
                    "section": question["section"],
                    "text": question["text"],
                    "type": "likert",
                    "counts": [
                        {
                            **option,
                            "count": counts[option["value"]],
                        }
                        for option in LIKERT_OPTIONS
                    ],
                    "answered": answered,
                    "average": round(score_total / answered, 2) if answered else 0,
                }
            )
        else:
            comments = [
                str(response.answers.get(question_id) or "").strip()
                for response in responses
                if str(response.answers.get(question_id) or "").strip()
            ]
            analytics.append(
                {
                    "id": question_id,
                    "section": question["section"],
                    "text": question["text"],
                    "type": "text",
                    "comments": comments,
                    "answered": len(comments),
                }
            )
    return analytics


def respondent_status(survey):
    response_map = {
        response.student_id: response
        for response in survey.responses.select_related("student", "student__user")
    }
    rows = []
    for enrollment in eligible_enrollments(survey):
        student = enrollment.student
        response = response_map.get(student.id)
        rows.append(
            {
                "id": student.id,
                "name": profile_display_name(student),
                "student_id": getattr(student, "student_id", "") or "",
                "email": student.user.email,
                "submitted": bool(response),
                "submitted_at": response.submitted_at.isoformat() if response else None,
            }
        )
    return rows


def serialize_survey_detail(survey):
    payload = serialize_survey(survey, include_questions=True)
    payload["respondents"] = respondent_status(survey)
    payload["analytics"] = response_analytics(survey)
    return payload


def validate_answers(survey, raw_answers):
    if not isinstance(raw_answers, dict):
        raise ValueError("Evaluation answers must be submitted as an object.")
    answers = {}
    for question in survey.questions or []:
        question_id = question["id"]
        raw_value = raw_answers.get(question_id)
        if question["type"] == "likert":
            value = str(raw_value or "").strip()
            if value and value not in LIKERT_VALUES:
                raise ValueError(f"Select a valid response for: {question['text']}")
        else:
            value = str(raw_value or "").strip()
        if question.get("required", True) and not value:
            raise ValueError(f"Please answer: {question['text']}")
        answers[question_id] = value
    return answers


def student_surveys(student):
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
            is_published=True,
            offering__enrollment__student=student,
        )
        .distinct()
        .order_by("-offering__semester__start_date", "offering__course__code")
    )


def serialize_student_survey(survey, student, include_questions=False):
    payload = serialize_survey(survey, include_questions=include_questions)
    response = survey.responses.filter(student=student).first()
    payload["submitted"] = bool(response)
    payload["submitted_at"] = response.submitted_at.isoformat() if response else None
    payload["answers"] = response.answers if response and include_questions else None
    return payload


def outstanding_required_surveys(student, target_semester=None):
    surveys = CourseEvaluationSurvey.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
    ).filter(
        is_published=True,
        is_required=True,
        offering__enrollment__student=student,
    ).exclude(responses__student=student)

    if target_semester:
        surveys = surveys.exclude(offering__semester=target_semester)
        if target_semester.start_date:
            surveys = surveys.filter(
                Q(offering__semester__start_date__lt=target_semester.start_date)
                | Q(offering__semester__start_date__isnull=True)
            )
        if target_semester.calendar_group:
            surveys = surveys.filter(
                offering__semester__calendar_group=target_semester.calendar_group
            )
    return surveys.distinct().order_by(
        "offering__semester__start_date",
        "offering__course__code",
    )


def registration_evaluation_gate(student, target_semester=None):
    pending = list(outstanding_required_surveys(student, target_semester=target_semester))
    return {
        "blocked": bool(pending),
        "pending_count": len(pending),
        "message": (
            "Complete all required SEC-SET course evaluations before registering for the next semester."
            if pending
            else ""
        ),
        "surveys": [
            {
                "id": survey.id,
                "title": survey.title,
                "course_code": survey.offering.course.code,
                "course_title": survey.offering.course.title,
                "semester": survey.offering.semester.name,
                "state": survey_state(survey),
                "url": f"/student/evaluations/{survey.id}",
            }
            for survey in pending
        ],
    }


def export_rows(survey):
    questions = survey.questions or []
    headers = [
        "Student ID",
        "Student Name",
        "Email",
        "Submission Status",
        "Submitted At",
        *[question["text"] for question in questions],
    ]
    response_map = {response.student_id: response for response in survey.responses.all()}
    rows = [headers]
    for enrollment in eligible_enrollments(survey):
        student = enrollment.student
        response = response_map.get(student.id)
        answers = response.answers if response else {}
        values = []
        for question in questions:
            value = answers.get(question["id"], "")
            values.append(LIKERT_LABELS.get(value, value))
        rows.append(
            [
                getattr(student, "student_id", "") or "",
                profile_display_name(student),
                student.user.email,
                "Submitted" if response else "Pending",
                response.submitted_at.isoformat() if response else "",
                *values,
            ]
        )
    return rows
