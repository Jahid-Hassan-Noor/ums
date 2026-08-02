import ipaddress
import random
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from admin_app.models import CourseOffering, Profile
from student_app.models import Enrollment
from student_app.registration_service import get_student_profile
from teacher_app.assignment_service import get_teacher_profile, profile_display_name, teacher_offerings

from quiz_app.models import (
    Question,
    QuestionAttempt,
    QuestionAttemptStep,
    QuestionBank,
    QuestionCategory,
    QuestionChoice,
    QuestionVersion,
    Quiz,
    QuizAccessOverride,
    QuizAttempt,
    QuizGrade,
    QuizQuestionSlot,
    QuizRandomRule,
    QuizSection,
)


SCORE_QUANT = Decimal("0.01")


class QuizWorkflowError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def decimal_value(value, default=None, *, minimum=None, maximum=None):
    if value in (None, ""):
        if default is not None:
            return Decimal(str(default)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
        return None
    try:
        parsed = Decimal(str(value)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise QuizWorkflowError("Scores and marks must be valid numbers.")
    if minimum is not None and parsed < Decimal(str(minimum)):
        raise QuizWorkflowError(f"Value must be at least {minimum}.")
    if maximum is not None and parsed > Decimal(str(maximum)):
        raise QuizWorkflowError(f"Value must be at most {maximum}.")
    return parsed


def bool_value(value, default=False):
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def int_value(value, default=0, *, minimum=0, maximum=None):
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise QuizWorkflowError("Numeric fields must be valid integers.")
    if parsed < minimum:
        raise QuizWorkflowError(f"Value must be at least {minimum}.")
    if maximum is not None and parsed > maximum:
        raise QuizWorkflowError(f"Value must be at most {maximum}.")
    return parsed


def datetime_value(value):
    if value in (None, ""):
        return None
    if hasattr(value, "isoformat"):
        return value
    parsed = parse_datetime(str(value))
    if not parsed:
        raise QuizWorkflowError("Date and time values must be valid ISO datetimes.")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def offering_payload(offering):
    return {
        "id": offering.id,
        "course_code": offering.course.code,
        "course_title": offering.course.title,
        "section": offering.section,
        "semester": offering.semester.name,
    }


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def teacher_quiz_queryset(profile):
    return (
        Quiz.objects.select_related("offering", "offering__course", "offering__semester", "created_by", "created_by__user")
        .filter(offering__in=teacher_offerings(profile))
        .annotate(attempt_count=Count("attempts", distinct=True))
        .order_by("-created_at")
    )


def quiz_for_teacher(profile, quiz_id):
    return (
        Quiz.objects.select_related("offering", "offering__course", "offering__semester", "created_by", "created_by__user")
        .filter(pk=quiz_id, offering__in=teacher_offerings(profile))
        .first()
    )


def student_quiz_queryset(student):
    offering_ids = Enrollment.objects.filter(student=student, completed_at__isnull=True).values("offering_id")
    now = timezone.now()
    return (
        Quiz.objects.select_related("offering", "offering__course", "offering__semester", "created_by", "created_by__user")
        .filter(offering_id__in=offering_ids, status=Quiz.STATUS_PUBLISHED)
        .filter(Q(opens_at__isnull=True) | Q(opens_at__lte=now))
        .order_by("closes_at", "title")
    )


def quiz_for_student(student, quiz_id):
    return student_quiz_queryset(student).filter(pk=quiz_id).first()


def default_bank_for_offering(offering, teacher):
    bank, _created = QuestionBank.objects.get_or_create(
        offering=offering,
        defaults={
            "course": offering.course,
            "title": f"{offering.course.code} {offering.section}".strip() + " Question Bank",
            "owner": teacher,
        },
    )
    if not bank.course_id:
        bank.course = offering.course
        bank.save(update_fields=["course", "updated_at"])
    return bank


def teacher_question_banks(teacher):
    offerings = teacher_offerings(teacher)
    for offering in offerings:
        default_bank_for_offering(offering, teacher)
    return (
        QuestionBank.objects.select_related("offering", "offering__course", "offering__semester", "course", "owner", "owner__user")
        .filter(Q(offering__in=offerings) | Q(owner=teacher))
        .distinct()
        .order_by("course__code", "offering__section", "title")
    )


def bank_for_teacher(teacher, bank_id):
    return teacher_question_banks(teacher).filter(pk=bank_id).first()


def question_for_teacher(teacher, question_id):
    return (
        Question.objects.select_related("bank", "bank__offering", "bank__course", "category", "created_by", "created_by__user")
        .prefetch_related("versions", "versions__choices")
        .filter(pk=question_id, bank__in=teacher_question_banks(teacher))
        .first()
    )


def category_payload(category):
    return {
        "id": category.id,
        "bank_id": category.bank_id,
        "parent_id": category.parent_id,
        "title": category.title,
        "description": category.description,
        "sort_order": category.sort_order,
    }


def bank_payload(bank):
    return {
        "id": bank.id,
        "title": bank.title,
        "description": bank.description,
        "offering": offering_payload(bank.offering) if bank.offering_id else None,
        "course": {
            "id": bank.course_id,
            "code": bank.course.code,
            "title": bank.course.title,
        }
        if bank.course_id
        else None,
        "owner": profile_display_name(bank.owner),
        "is_shared": bank.is_shared,
        "question_count": getattr(bank, "question_count", bank.questions.count()),
    }


def question_payload(question, *, include_versions=False):
    versions = list(question.versions.prefetch_related("choices").all())
    latest = versions[0] if versions else latest_ready_version(question)
    payload = {
        "id": question.id,
        "bank_id": question.bank_id,
        "bank_title": question.bank.title,
        "category": category_payload(question.category) if question.category_id else None,
        "title": question.title,
        "question_type": question.question_type,
        "question_type_label": question.get_question_type_display(),
        "tags": question.tags,
        "difficulty": question.difficulty,
        "created_by": profile_display_name(question.created_by),
        "latest_version": question_version_payload(latest, include_answers=True) if latest else None,
        "version_count": len(versions),
    }
    if include_versions:
        payload["versions"] = [question_version_payload(version, include_answers=True) for version in versions]
    return payload


def question_option_payload(question):
    latest = latest_ready_version(question)
    if not latest:
        return None
    return {
        "id": question.id,
        "version_id": latest.id,
        "bank_id": question.bank_id,
        "title": question.title,
        "question_type": question.question_type,
        "question_type_label": question.get_question_type_display(),
        "default_mark": str(latest.default_mark),
    }


def question_bank_options_payload(teacher, offering=None):
    banks = teacher_question_banks(teacher)
    if offering:
        banks = banks.filter(Q(offering=offering) | Q(owner=teacher))
    bank_ids = banks.values("id")
    questions = (
        Question.objects.select_related("bank")
        .prefetch_related("versions", "versions__choices")
        .filter(bank_id__in=bank_ids)
        .order_by("title")
    )
    return {
        "question_banks": [bank_payload(bank) for bank in banks.annotate(question_count=Count("questions", distinct=True))],
        "question_bank_questions": [item for item in (question_option_payload(question) for question in questions) if item],
        "question_types": question_type_metadata(),
    }


def teacher_question_bank_payload(teacher):
    banks = teacher_question_banks(teacher).annotate(question_count=Count("questions", distinct=True))
    bank_ids = banks.values("id")
    categories = QuestionCategory.objects.filter(bank_id__in=bank_ids).select_related("bank", "parent")
    questions = (
        Question.objects.select_related("bank", "category", "created_by", "created_by__user")
        .prefetch_related("versions", "versions__choices")
        .filter(bank_id__in=bank_ids)
        .order_by("bank__title", "category__title", "title")
    )
    return {
        "offerings": [offering_payload(offering) for offering in teacher_offerings(teacher)],
        "banks": [bank_payload(bank) for bank in banks],
        "categories": [category_payload(category) for category in categories],
        "questions": [question_payload(question, include_versions=True) for question in questions],
        "question_types": question_type_metadata(),
    }


def latest_ready_version(question):
    return question.versions.filter(status=QuestionVersion.STATUS_READY).order_by("-version").first()


def question_type_metadata():
    auto_graded = {
        Question.TYPE_MULTIPLE_CHOICE,
        Question.TYPE_TRUE_FALSE,
        Question.TYPE_SHORT_ANSWER,
        Question.TYPE_FILL_BLANK,
        Question.TYPE_NUMERICAL,
        Question.TYPE_MATCHING,
        Question.TYPE_ORDERING,
    }
    return [
        {
            "value": value,
            "label": label,
            "auto_graded": value in auto_graded,
            "needs_choices": value == Question.TYPE_MULTIPLE_CHOICE,
            "needs_correct_answer": value
            in {
                Question.TYPE_TRUE_FALSE,
                Question.TYPE_SHORT_ANSWER,
                Question.TYPE_FILL_BLANK,
                Question.TYPE_NUMERICAL,
            },
            "needs_settings": value in {Question.TYPE_NUMERICAL, Question.TYPE_MATCHING, Question.TYPE_ORDERING},
        }
        for value, label in Question.TYPE_CHOICES
    ]


def question_version_payload(version, *, include_answers=False):
    choices = list(version.choices.all())
    settings = version.settings or {}
    payload = {
        "id": version.id,
        "question_id": version.question_id,
        "question_title": version.question.title,
        "question_type": version.question.question_type,
        "question_type_label": version.question.get_question_type_display(),
        "version": version.version,
        "status": version.status,
        "question_text": version.question_text,
        "default_mark": str(version.default_mark),
        "general_feedback": version.general_feedback if include_answers else "",
        "choices": [
            {
                "id": choice.id,
                "label": choice.label,
                "text": choice.text,
                "feedback": choice.feedback if include_answers else "",
                "is_correct": choice.is_correct if include_answers else False,
            }
            for choice in choices
        ],
    }
    if version.question.question_type == Question.TYPE_MATCHING and not include_answers:
        answers = [pair.get("answer", "") for pair in settings.get("pairs", [])]
        random.Random(version.id).shuffle(answers)
        payload["settings"] = {
            "prompts": [pair.get("prompt", "") for pair in settings.get("pairs", [])],
            "answers": answers,
        }
    elif version.question.question_type == Question.TYPE_ORDERING and not include_answers:
        items = list(settings.get("items", []))
        random.Random(version.id).shuffle(items)
        payload["settings"] = {"items": items}
    if include_answers:
        payload["correct_answer"] = version.correct_answer
        payload["settings"] = settings
    return payload


def slot_payload(slot, *, include_answers=False):
    return {
        "id": slot.id,
        "section_id": slot.section_id,
        "question_version": question_version_payload(slot.question_version, include_answers=include_answers),
        "sort_order": slot.sort_order,
        "page": slot.page,
        "display_number": slot.display_number,
        "max_mark": str(slot.max_mark),
        "require_previous": slot.require_previous,
    }


def random_rule_payload(rule):
    return {
        "id": rule.id,
        "section_id": rule.section_id,
        "category_id": rule.category_id,
        "category": rule.category.title if rule.category_id else "",
        "question_type": rule.question_type,
        "count": rule.count,
        "max_mark": str(rule.max_mark),
        "sort_order": rule.sort_order,
    }


def quiz_statistics_payload(quiz):
    attempts = list(quiz.attempts.select_related("student", "student__user").all())
    scores = [attempt.score for attempt in attempts if attempt.score is not None]
    submitted = [attempt for attempt in attempts if attempt.state in {QuizAttempt.STATE_SUBMITTED, QuizAttempt.STATE_OVERDUE}]
    question_stats = {}
    for question_attempt in quiz.question_attempts.select_related("question_version", "question_version__question").all():
        key = question_attempt.question_version_id
        record = question_stats.setdefault(
            key,
            {
                "question_version_id": key,
                "question_text": question_attempt.question_version.question_text,
                "question_type": question_attempt.question_version.question.question_type,
                "attempts": 0,
                "answered": 0,
                "manual_pending": 0,
                "full_mark": 0,
                "total_awarded": Decimal("0.00"),
                "max_mark": question_attempt.max_mark,
            },
        )
        record["attempts"] += 1
        if question_attempt.response_summary:
            record["answered"] += 1
        if question_attempt.requires_manual_grading:
            record["manual_pending"] += 1
        if question_attempt.awarded_mark is not None:
            record["total_awarded"] += question_attempt.awarded_mark
            if question_attempt.awarded_mark >= question_attempt.max_mark:
                record["full_mark"] += 1
    return {
        "attempts_total": len(attempts),
        "attempts_submitted": len(submitted),
        "attempts_in_progress": sum(1 for attempt in attempts if attempt.state == QuizAttempt.STATE_IN_PROGRESS),
        "manual_pending": sum(1 for attempt in attempts if attempt.needs_manual_grading),
        "average_score": str((sum(scores, Decimal("0.00")) / len(scores)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)) if scores else None,
        "highest_score": str(max(scores).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)) if scores else None,
        "lowest_score": str(min(scores).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)) if scores else None,
        "questions": [
            {
                **record,
                "max_mark": str(record["max_mark"]),
                "total_awarded": str(record["total_awarded"].quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)),
                "average_mark": str((record["total_awarded"] / record["attempts"]).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP))
                if record["attempts"]
                else None,
            }
            for record in question_stats.values()
        ],
    }


def quiz_payload(quiz, *, include_detail=False, include_teacher=False, student=None):
    attempts = []
    if student:
        attempts = [
            attempt_payload(attempt, include_questions=False)
            for attempt in quiz.attempts.filter(student=student).order_by("attempt_number")
        ]
    payload = {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "instructions": quiz.instructions,
        "status": quiz.status,
        "status_label": quiz.get_status_display(),
        "opens_at": quiz.opens_at.isoformat() if quiz.opens_at else None,
        "closes_at": quiz.closes_at.isoformat() if quiz.closes_at else None,
        "time_limit_minutes": quiz.time_limit_minutes,
        "max_attempts": quiz.max_attempts,
        "grade_method": quiz.grade_method,
        "grade_method_label": quiz.get_grade_method_display(),
        "total_marks": str(quiz.total_marks),
        "pass_mark": str(quiz.pass_mark),
        "shuffle_questions": quiz.shuffle_questions,
        "shuffle_answers": quiz.shuffle_answers,
        "require_safe_exam_browser": quiz.require_safe_exam_browser,
        "review_show_attempt": quiz.review_show_attempt,
        "review_show_marks": quiz.review_show_marks,
        "review_show_correctness": quiz.review_show_correctness,
        "review_show_right_answer": quiz.review_show_right_answer,
        "review_show_feedback": quiz.review_show_feedback,
        "created_by": profile_display_name(quiz.created_by),
        "offering": offering_payload(quiz.offering),
        "attempt_count": getattr(quiz, "attempt_count", quiz.attempts.count()),
        "student_attempts": attempts,
    }
    if include_teacher:
        payload["password_required"] = bool(quiz.password)
        payload["ip_allowlist"] = quiz.ip_allowlist
        payload["safe_exam_browser_config_key"] = quiz.safe_exam_browser_config_key
    if include_detail:
        payload["sections"] = [
            {
                "id": section.id,
                "title": section.title,
                "sort_order": section.sort_order,
                "shuffle_questions": section.shuffle_questions,
            }
            for section in quiz.sections.all()
        ]
        payload["slots"] = [slot_payload(slot, include_answers=include_teacher) for slot in quiz.question_slots.all()]
        payload["random_rules"] = [random_rule_payload(rule) for rule in quiz.random_rules.all()]
        if include_teacher:
            payload["statistics"] = quiz_statistics_payload(quiz)
            payload["attempts"] = [
                attempt_payload(attempt, include_questions=True, review=True, teacher=True)
                for attempt in quiz.attempts.select_related("student", "student__user").order_by("-started_at")
            ]
    return payload


def parse_line_pairs(value):
    if isinstance(value, list):
        pairs = value
    else:
        pairs = []
        for line in str(value or "").splitlines():
            if not line.strip():
                continue
            prompt, separator, answer = line.partition("|")
            pairs.append({"prompt": prompt.strip(), "answer": answer.strip() if separator else ""})
    return [
        {"prompt": str(item.get("prompt", "")).strip(), "answer": str(item.get("answer", "")).strip()}
        for item in pairs
        if str(item.get("prompt", "")).strip() or str(item.get("answer", "")).strip()
    ]


def parse_line_items(value):
    if isinstance(value, list):
        items = value
    else:
        items = str(value or "").splitlines()
    return [str(item).strip() for item in items if str(item).strip()]


def parse_matching_answer(value):
    pairs = {}
    for item in parse_line_pairs(value):
        if item["prompt"]:
            pairs[item["prompt"]] = item["answer"]
    return pairs


def question_settings_from_payload(question_type, data):
    source = data.get("settings") if isinstance(data.get("settings"), dict) else {}
    settings = dict(source)
    if question_type == Question.TYPE_NUMERICAL:
        settings["tolerance"] = str(decimal_value(data.get("tolerance", settings.get("tolerance", 0)), default=0, minimum=0))
    elif question_type == Question.TYPE_MATCHING:
        settings["pairs"] = parse_line_pairs(data.get("matching_pairs", settings.get("pairs", [])))
    elif question_type == Question.TYPE_ORDERING:
        settings["items"] = parse_line_items(data.get("ordering_items", settings.get("items", [])))
    return settings


def create_question_version(question, teacher, data):
    question_type = question.question_type
    next_version = (question.versions.order_by("-version").values_list("version", flat=True).first() or 0) + 1
    version = QuestionVersion.objects.create(
        question=question,
        version=next_version,
        status=str(data.get("status", QuestionVersion.STATUS_READY)).strip() or QuestionVersion.STATUS_READY,
        question_text=str(data.get("question_text", "")).strip(),
        default_mark=decimal_value(data.get("default_mark", data.get("max_mark")), default=1, minimum=0),
        general_feedback=str(data.get("general_feedback", "")).strip(),
        correct_answer=str(data.get("correct_answer", "")).strip(),
        settings=question_settings_from_payload(question_type, data),
        created_by=teacher,
    )
    for index, choice_data in enumerate(data.get("choices") or [], start=1):
        QuestionChoice.objects.create(
            question_version=version,
            label=str(choice_data.get("label") or chr(64 + index)).strip(),
            text=str(choice_data.get("text", "")).strip(),
            is_correct=bool_value(choice_data.get("is_correct")),
            feedback=str(choice_data.get("feedback", "")).strip(),
            sort_order=index,
        )
    validate_question_version(version)
    return version


def create_or_update_question(bank, teacher, data):
    question_type = str(data.get("question_type", Question.TYPE_MULTIPLE_CHOICE)).strip()
    if question_type not in {value for value, _label in Question.TYPE_CHOICES}:
        raise QuizWorkflowError("Unsupported question type.")
    category = None
    category_title = str(data.get("category", "")).strip()
    if data.get("category_id"):
        category = QuestionCategory.objects.filter(pk=data.get("category_id"), bank=bank).first()
    elif category_title:
        category, _created = QuestionCategory.objects.get_or_create(
            bank=bank,
            parent=None,
            title=category_title,
        )
    question = Question.objects.create(
        bank=bank,
        category=category,
        title=str(data.get("title") or data.get("question_text") or "Question").strip(),
        question_type=question_type,
        tags=data.get("tags") or [],
        difficulty=str(data.get("difficulty", "")).strip(),
        created_by=teacher,
    )
    version = create_question_version(question, teacher, data)
    return question, version


def validate_question_version(version):
    qtype = version.question.question_type
    if not version.question_text.strip():
        raise QuizWorkflowError("Question text is required.")
    if qtype == Question.TYPE_MULTIPLE_CHOICE:
        choices = list(version.choices.all())
        if len(choices) < 2:
            raise QuizWorkflowError("Multiple-choice questions need at least two choices.")
        if not any(choice.is_correct for choice in choices):
            raise QuizWorkflowError("Multiple-choice questions need at least one correct choice.")
    if qtype in {Question.TYPE_TRUE_FALSE, Question.TYPE_SHORT_ANSWER, Question.TYPE_FILL_BLANK, Question.TYPE_NUMERICAL} and not version.correct_answer.strip():
        raise QuizWorkflowError("This question type needs a correct answer.")
    if qtype == Question.TYPE_NUMERICAL:
        decimal_value(version.correct_answer, minimum=None)
        decimal_value((version.settings or {}).get("tolerance", 0), default=0, minimum=0)
    if qtype == Question.TYPE_MATCHING:
        pairs = (version.settings or {}).get("pairs", [])
        if len(pairs) < 2 or any(not item.get("prompt") or not item.get("answer") for item in pairs):
            raise QuizWorkflowError("Matching questions need at least two prompt-answer pairs.")
    if qtype == Question.TYPE_ORDERING:
        items = (version.settings or {}).get("items", [])
        if len(items) < 2:
            raise QuizWorkflowError("Ordering questions need at least two ordered items.")


def create_quiz_from_payload(teacher, data):
    offering = teacher_offerings(teacher).filter(pk=data.get("offering_id")).first()
    if not offering:
        raise QuizWorkflowError("Course offering not found for this teacher.", status_code=404)

    with transaction.atomic():
        quiz = Quiz.objects.create(
            offering=offering,
            title=str(data.get("title", "")).strip(),
            description=str(data.get("description", "")).strip(),
            instructions=str(data.get("instructions", "")).strip(),
            status=str(data.get("status", Quiz.STATUS_DRAFT)).strip() or Quiz.STATUS_DRAFT,
            opens_at=datetime_value(data.get("opens_at")),
            closes_at=datetime_value(data.get("closes_at")),
            time_limit_minutes=int_value(data.get("time_limit_minutes"), default=0),
            max_attempts=int_value(data.get("max_attempts"), default=1, minimum=0, maximum=50),
            password=str(data.get("password", "")).strip(),
            ip_allowlist=str(data.get("ip_allowlist", "")).strip(),
            require_safe_exam_browser=bool_value(data.get("require_safe_exam_browser")),
            safe_exam_browser_config_key=str(data.get("safe_exam_browser_config_key", "")).strip(),
            grade_method=str(data.get("grade_method", Quiz.GRADE_HIGHEST)).strip() or Quiz.GRADE_HIGHEST,
            pass_mark=decimal_value(data.get("pass_mark"), default=0, minimum=0),
            shuffle_questions=bool_value(data.get("shuffle_questions")),
            shuffle_answers=bool_value(data.get("shuffle_answers")),
            review_show_attempt=bool_value(data.get("review_show_attempt"), True),
            review_show_marks=bool_value(data.get("review_show_marks"), True),
            review_show_correctness=bool_value(data.get("review_show_correctness")),
            review_show_right_answer=bool_value(data.get("review_show_right_answer")),
            review_show_feedback=bool_value(data.get("review_show_feedback"), True),
            created_by=teacher,
        )
        if not quiz.title:
            raise QuizWorkflowError("Quiz title is required.")
        if quiz.status not in {value for value, _label in Quiz.STATUS_CHOICES}:
            raise QuizWorkflowError("Invalid quiz status.")
        if quiz.grade_method not in {value for value, _label in Quiz.GRADE_CHOICES}:
            raise QuizWorkflowError("Invalid grade method.")

        section = QuizSection.objects.create(quiz=quiz, title="", sort_order=0)
        bank = default_bank_for_offering(offering, teacher)
        for index, question_data in enumerate(data.get("questions") or [], start=1):
            _question, version = create_or_update_question(bank, teacher, question_data)
            QuizQuestionSlot.objects.create(
                quiz=quiz,
                section=section,
                question_version=version,
                sort_order=index,
                page=int_value(question_data.get("page"), default=1, minimum=1),
                display_number=str(question_data.get("display_number", "")).strip(),
                max_mark=decimal_value(question_data.get("max_mark"), default=version.default_mark, minimum=0),
                require_previous=bool_value(question_data.get("require_previous")),
            )
        recalculate_quiz_total(quiz)
        return quiz


def update_quiz_from_payload(quiz, data):
    editable_fields = {
        "title",
        "description",
        "instructions",
        "status",
        "opens_at",
        "closes_at",
        "password",
        "ip_allowlist",
        "safe_exam_browser_config_key",
        "grade_method",
    }
    for field in editable_fields:
        if field in data:
            setattr(
                quiz,
                field,
                str(data.get(field, "")).strip()
                if field not in {"opens_at", "closes_at"}
                else datetime_value(data.get(field)),
            )
    for field in [
        "time_limit_minutes",
        "max_attempts",
    ]:
        if field in data:
            setattr(quiz, field, int_value(data.get(field), default=getattr(quiz, field)))
    for field in ["pass_mark"]:
        if field in data:
            setattr(quiz, field, decimal_value(data.get(field), default=getattr(quiz, field), minimum=0))
    for field in [
        "shuffle_questions",
        "shuffle_answers",
        "require_safe_exam_browser",
        "review_show_attempt",
        "review_show_marks",
        "review_show_correctness",
        "review_show_right_answer",
        "review_show_feedback",
    ]:
        if field in data:
            setattr(quiz, field, bool_value(data.get(field), getattr(quiz, field)))
    quiz.full_clean()
    quiz.save()
    return quiz


def create_question_category(teacher, data):
    bank = bank_for_teacher(teacher, data.get("bank_id"))
    if not bank:
        raise QuizWorkflowError("Question bank not found.", status_code=404)
    parent = None
    if data.get("parent_id"):
        parent = QuestionCategory.objects.filter(pk=data.get("parent_id"), bank=bank).first()
        if not parent:
            raise QuizWorkflowError("Parent category not found.", status_code=404)
    title = str(data.get("title", "")).strip()
    if not title:
        raise QuizWorkflowError("Category title is required.")
    category, _created = QuestionCategory.objects.get_or_create(
        bank=bank,
        parent=parent,
        title=title,
        defaults={
            "description": str(data.get("description", "")).strip(),
            "sort_order": int_value(data.get("sort_order"), default=0, minimum=0),
        },
    )
    return category


def create_bank_question(teacher, data):
    bank = bank_for_teacher(teacher, data.get("bank_id"))
    if not bank and data.get("offering_id"):
        offering = teacher_offerings(teacher).filter(pk=data.get("offering_id")).first()
        if not offering:
            raise QuizWorkflowError("Course offering not found for this teacher.", status_code=404)
        bank = default_bank_for_offering(offering, teacher)
    if not bank:
        raise QuizWorkflowError("Question bank not found.", status_code=404)
    return create_or_update_question(bank, teacher, data)


def create_new_question_version(teacher, question_id, data):
    question = question_for_teacher(teacher, question_id)
    if not question:
        raise QuizWorkflowError("Question not found.", status_code=404)
    if data.get("title"):
        question.title = str(data.get("title", "")).strip()
    if data.get("category_id"):
        category = QuestionCategory.objects.filter(pk=data.get("category_id"), bank=question.bank).first()
        if not category:
            raise QuizWorkflowError("Question category not found.", status_code=404)
        question.category = category
    question.save(update_fields=["title", "category", "updated_at"])
    return create_question_version(question, teacher, data)


def version_for_teacher(teacher, *, question_id=None, version_id=None):
    versions = QuestionVersion.objects.select_related("question", "question__bank").prefetch_related("choices")
    if version_id:
        versions = versions.filter(pk=version_id)
    elif question_id:
        versions = versions.filter(question_id=question_id, status=QuestionVersion.STATUS_READY).order_by("-version")
    else:
        raise QuizWorkflowError("Question selection is required.")
    version = versions.filter(question__bank__in=teacher_question_banks(teacher)).first()
    if not version:
        raise QuizWorkflowError("Question not found.", status_code=404)
    return version


def add_question_to_quiz(quiz, teacher, data):
    bank = default_bank_for_offering(quiz.offering, teacher)
    with transaction.atomic():
        if data.get("question_version_id") or data.get("question_id"):
            version = version_for_teacher(
                teacher,
                question_id=data.get("question_id"),
                version_id=data.get("question_version_id"),
            )
        else:
            _question, version = create_or_update_question(bank, teacher, data)
        next_order = (quiz.question_slots.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0) + 1
        section = quiz.sections.order_by("sort_order", "id").first() or QuizSection.objects.create(quiz=quiz, title="", sort_order=0)
        slot = QuizQuestionSlot.objects.create(
            quiz=quiz,
            section=section,
            question_version=version,
            sort_order=int_value(data.get("sort_order"), default=next_order, minimum=1),
            page=int_value(data.get("page"), default=1, minimum=1),
            display_number=str(data.get("display_number", "")).strip(),
            max_mark=decimal_value(data.get("max_mark"), default=version.default_mark, minimum=0),
            require_previous=bool_value(data.get("require_previous")),
        )
        recalculate_quiz_total(quiz)
        return slot


def add_random_rule_to_quiz(quiz, data):
    question_type = str(data.get("question_type", "")).strip()
    if question_type and question_type not in {value for value, _label in Question.TYPE_CHOICES}:
        raise QuizWorkflowError("Unsupported question type.")
    category = None
    if data.get("category_id"):
        category = QuestionCategory.objects.filter(
            pk=data.get("category_id"),
            bank__offering=quiz.offering,
        ).first()
        if not category:
            raise QuizWorkflowError("Question category not found.", status_code=404)
    next_order = (quiz.random_rules.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0) + 1
    section = quiz.sections.order_by("sort_order", "id").first() or QuizSection.objects.create(quiz=quiz, title="", sort_order=0)
    with transaction.atomic():
        rule = QuizRandomRule.objects.create(
            quiz=quiz,
            section=section,
            category=category,
            question_type=question_type,
            count=int_value(data.get("count"), default=1, minimum=1, maximum=100),
            max_mark=decimal_value(data.get("max_mark"), default=1, minimum=0),
            sort_order=int_value(data.get("sort_order"), default=next_order, minimum=1),
        )
        recalculate_quiz_total(quiz)
        return rule


def recalculate_quiz_total(quiz):
    total = sum((slot.max_mark for slot in quiz.question_slots.all()), Decimal("0.00"))
    total += sum((rule.max_mark * rule.count for rule in quiz.random_rules.all()), Decimal("0.00"))
    quiz.total_marks = total.quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    quiz.save(update_fields=["total_marks", "updated_at"])


def access_override_for(quiz, student):
    return quiz.access_overrides.filter(student=student).first()


def effective_quiz_setting(quiz, override, field):
    value = getattr(override, field, None) if override else None
    return getattr(quiz, field) if value in (None, "") else value


def ip_allowed(quiz, ip_address):
    raw = quiz.ip_allowlist.strip()
    if not raw:
        return True
    if not ip_address:
        return False
    try:
        address = ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    entries = [entry.strip() for item in raw.splitlines() for entry in item.split(",") if entry.strip()]
    for entry in entries:
        try:
            if "/" in entry:
                if address in ipaddress.ip_network(entry, strict=False):
                    return True
            elif address == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


def safe_exam_browser_allowed(quiz, config_key=""):
    if not quiz.require_safe_exam_browser:
        return True
    if not quiz.safe_exam_browser_config_key:
        return bool(config_key)
    return str(config_key or "").strip() == quiz.safe_exam_browser_config_key


def start_access_status(quiz, student, *, password="", ip_address="", safe_exam_browser_key=""):
    now = timezone.now()
    override = access_override_for(quiz, student)
    opens_at = effective_quiz_setting(quiz, override, "opens_at")
    closes_at = effective_quiz_setting(quiz, override, "closes_at")
    max_attempts = effective_quiz_setting(quiz, override, "max_attempts")
    required_password = effective_quiz_setting(quiz, override, "password")

    if quiz.status != Quiz.STATUS_PUBLISHED:
        return False, "Quiz is not published."
    if opens_at and now < opens_at:
        return False, "Quiz is not open yet."
    if closes_at and now > closes_at:
        return False, "Quiz is closed."
    if required_password and str(password or "") != required_password:
        return False, "Quiz password is required or incorrect."
    if not ip_allowed(quiz, ip_address):
        return False, "This network is not allowed for this quiz."
    if not safe_exam_browser_allowed(quiz, safe_exam_browser_key):
        return False, "Safe Exam Browser is required for this quiz."
    attempts_count = QuizAttempt.objects.filter(quiz=quiz, student=student).count()
    if max_attempts and attempts_count >= max_attempts:
        return False, "Maximum attempts reached."
    return True, ""


def attempt_time_limit(quiz, student):
    override = access_override_for(quiz, student)
    return effective_quiz_setting(quiz, override, "time_limit_minutes") or 0


def attempt_close_time(quiz, student):
    override = access_override_for(quiz, student)
    return effective_quiz_setting(quiz, override, "closes_at")


def selected_versions_for_random_rule(rule, exclude_ids):
    versions = (
        QuestionVersion.objects.select_related("question")
        .filter(status=QuestionVersion.STATUS_READY, question__bank__offering=rule.quiz.offering)
        .exclude(pk__in=exclude_ids)
    )
    if rule.category_id:
        versions = versions.filter(question__category=rule.category)
    if rule.question_type:
        versions = versions.filter(question__question_type=rule.question_type)
    candidates = list(versions)
    if len(candidates) < rule.count:
        raise QuizWorkflowError("Not enough ready questions for a random-question rule.")
    return random.sample(candidates, rule.count)


@transaction.atomic
def start_quiz_attempt(quiz, student, *, password="", ip_address="", safe_exam_browser_key=""):
    can_start, reason = start_access_status(
        quiz,
        student,
        password=password,
        ip_address=ip_address,
        safe_exam_browser_key=safe_exam_browser_key,
    )
    if not can_start:
        raise QuizWorkflowError(reason, status_code=403)
    attempt_number = QuizAttempt.objects.filter(quiz=quiz, student=student).count() + 1
    now = timezone.now()
    limit_minutes = attempt_time_limit(quiz, student)
    close_time = attempt_close_time(quiz, student)
    due_at = now + timezone.timedelta(minutes=limit_minutes) if limit_minutes else None
    if due_at and close_time:
        due_at = min(due_at, close_time)
    elif close_time:
        due_at = close_time
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=student,
        attempt_number=attempt_number,
        due_at=due_at,
    )
    fixed_slots = list(quiz.question_slots.select_related("question_version", "question_version__question").all())
    if quiz.shuffle_questions:
        random.shuffle(fixed_slots)
    slot_number = 1
    selected_ids = set()
    for slot in fixed_slots:
        selected_ids.add(slot.question_version_id)
        QuestionAttempt.objects.create(
            attempt=attempt,
            quiz=quiz,
            slot=slot,
            question_version=slot.question_version,
            slot_number=slot_number,
            max_mark=slot.max_mark,
        )
        slot_number += 1
    for rule in quiz.random_rules.select_related("category").all():
        for version in selected_versions_for_random_rule(rule, selected_ids):
            selected_ids.add(version.id)
            QuestionAttempt.objects.create(
                attempt=attempt,
                quiz=quiz,
                random_rule=rule,
                question_version=version,
                slot_number=slot_number,
                max_mark=rule.max_mark,
            )
            slot_number += 1
    if slot_number == 1:
        raise QuizWorkflowError("Quiz has no questions.")
    return attempt


def attempt_for_student(student, attempt_id):
    return (
        QuizAttempt.objects.select_related("quiz", "quiz__offering", "quiz__offering__course", "quiz__offering__semester", "student", "student__user")
        .filter(pk=attempt_id, student=student)
        .first()
    )


def attempt_for_teacher(teacher, attempt_id):
    return (
        QuizAttempt.objects.select_related("quiz", "quiz__offering", "quiz__offering__course", "quiz__offering__semester", "student", "student__user")
        .filter(pk=attempt_id, quiz__offering__in=teacher_offerings(teacher))
        .first()
    )


def ensure_attempt_mutable(attempt):
    if attempt.state != QuizAttempt.STATE_IN_PROGRESS:
        raise QuizWorkflowError("This attempt is no longer editable.", status_code=409)
    if attempt.due_at and timezone.now() > attempt.due_at:
        attempt.state = QuizAttempt.STATE_OVERDUE
        attempt.save(update_fields=["state", "updated_at"])
        raise QuizWorkflowError("Attempt time has expired. Submit the attempt for grading.", status_code=409)


def response_summary(version, response):
    qtype = version.question.question_type
    if qtype == Question.TYPE_MULTIPLE_CHOICE:
        ids = response.get("choice_ids") or []
        if response.get("choice_id"):
            ids = [response.get("choice_id")]
        labels = list(version.choices.filter(id__in=ids).values_list("label", flat=True))
        return ", ".join(labels)
    if qtype == Question.TYPE_MATCHING:
        matching = response.get("matching") or parse_matching_answer(response.get("answer", ""))
        return "; ".join(f"{prompt}: {answer}" for prompt, answer in matching.items())
    if qtype == Question.TYPE_ORDERING:
        order = response.get("order") or parse_line_items(response.get("answer", ""))
        return " > ".join(str(item) for item in order)
    return str(response.get("answer", "")).strip()


def right_answer_summary(version):
    qtype = version.question.question_type
    if qtype == Question.TYPE_MULTIPLE_CHOICE:
        return ", ".join(version.choices.filter(is_correct=True).values_list("label", flat=True))
    if qtype == Question.TYPE_MATCHING:
        return "; ".join(f"{pair.get('prompt')}: {pair.get('answer')}" for pair in (version.settings or {}).get("pairs", []))
    if qtype == Question.TYPE_ORDERING:
        return " > ".join((version.settings or {}).get("items", []))
    return version.correct_answer


def next_step_number(question_attempt):
    return (question_attempt.steps.order_by("-sequence_number").values_list("sequence_number", flat=True).first() or 0) + 1


def save_question_response(question_attempt, response, *, actor, ip_address="", state=QuestionAttemptStep.STATE_AUTOSAVED):
    question_attempt.response = response or {}
    question_attempt.response_summary = response_summary(question_attempt.question_version, question_attempt.response)
    question_attempt.save(update_fields=["response", "response_summary", "updated_at"])
    QuestionAttemptStep.objects.create(
        question_attempt=question_attempt,
        sequence_number=next_step_number(question_attempt),
        state=state,
        response=question_attempt.response,
        actor=actor,
        ip_address=ip_address or None,
    )
    return question_attempt


def answer_attempt_question(attempt, question_attempt_id, response, *, actor, ip_address=""):
    ensure_attempt_mutable(attempt)
    question_attempt = attempt.question_attempts.select_related("question_version", "question_version__question").filter(pk=question_attempt_id).first()
    if not question_attempt:
        raise QuizWorkflowError("Question attempt not found.", status_code=404)
    return save_question_response(question_attempt, response, actor=actor, ip_address=ip_address)


def normalize_answer(value):
    return str(value or "").strip().casefold()


def grade_question_attempt(question_attempt, *, manual=False):
    version = question_attempt.question_version
    qtype = version.question.question_type
    response = question_attempt.response or {}
    max_mark = question_attempt.max_mark
    question_attempt.right_answer_summary = right_answer_summary(version)
    question_attempt.requires_manual_grading = False

    if qtype == Question.TYPE_MULTIPLE_CHOICE:
        submitted = set(int(choice_id) for choice_id in response.get("choice_ids") or ([] if not response.get("choice_id") else [response.get("choice_id")]))
        correct = set(version.choices.filter(is_correct=True).values_list("id", flat=True))
        question_attempt.awarded_mark = max_mark if submitted and submitted == correct else Decimal("0.00")
    elif qtype == Question.TYPE_TRUE_FALSE:
        submitted = normalize_answer(response.get("answer"))
        correct = normalize_answer(version.correct_answer)
        question_attempt.awarded_mark = max_mark if submitted == correct else Decimal("0.00")
    elif qtype in {Question.TYPE_SHORT_ANSWER, Question.TYPE_FILL_BLANK}:
        submitted = normalize_answer(response.get("answer"))
        accepted = [normalize_answer(item) for item in version.correct_answer.split("|") if item.strip()]
        if submitted and submitted in accepted:
            question_attempt.awarded_mark = max_mark
        elif submitted:
            question_attempt.requires_manual_grading = True
            if question_attempt.awarded_mark is None:
                question_attempt.awarded_mark = Decimal("0.00")
        else:
            question_attempt.awarded_mark = Decimal("0.00")
    elif qtype == Question.TYPE_NUMERICAL:
        try:
            submitted = decimal_value(response.get("answer"), default=None)
        except QuizWorkflowError:
            submitted = None
        correct = decimal_value(version.correct_answer)
        tolerance = decimal_value((version.settings or {}).get("tolerance", 0), default=0, minimum=0)
        question_attempt.awarded_mark = max_mark if submitted is not None and abs(submitted - correct) <= tolerance else Decimal("0.00")
    elif qtype == Question.TYPE_MATCHING:
        submitted = response.get("matching") or parse_matching_answer(response.get("answer", ""))
        correct = {
            str(pair.get("prompt", "")).strip(): normalize_answer(pair.get("answer"))
            for pair in (version.settings or {}).get("pairs", [])
            if str(pair.get("prompt", "")).strip()
        }
        normalized = {str(prompt).strip(): normalize_answer(answer) for prompt, answer in submitted.items()}
        question_attempt.awarded_mark = max_mark if normalized and normalized == correct else Decimal("0.00")
    elif qtype == Question.TYPE_ORDERING:
        submitted = response.get("order") or parse_line_items(response.get("answer", ""))
        correct = [normalize_answer(item) for item in (version.settings or {}).get("items", [])]
        normalized = [normalize_answer(item) for item in submitted]
        question_attempt.awarded_mark = max_mark if normalized and normalized == correct else Decimal("0.00")
    else:
        question_attempt.requires_manual_grading = True
        if question_attempt.awarded_mark is None:
            question_attempt.awarded_mark = Decimal("0.00")

    fields = [
        "right_answer_summary",
        "requires_manual_grading",
        "awarded_mark",
        "updated_at",
    ]
    question_attempt.save(update_fields=fields)
    if manual:
        QuestionAttemptStep.objects.create(
            question_attempt=question_attempt,
            sequence_number=next_step_number(question_attempt),
            state=QuestionAttemptStep.STATE_GRADED,
            response=question_attempt.response,
            fraction=(question_attempt.awarded_mark / max_mark) if max_mark else Decimal("0.0000"),
            actor=question_attempt.manually_graded_by,
        )
    return question_attempt


def recompute_attempt_score(attempt):
    attempts = list(attempt.question_attempts.all())
    score = sum((qa.awarded_mark or Decimal("0.00") for qa in attempts), Decimal("0.00"))
    needs_manual = any(qa.requires_manual_grading for qa in attempts)
    attempt.score = score.quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    attempt.needs_manual_grading = needs_manual
    attempt.save(update_fields=["score", "needs_manual_grading", "updated_at"])
    return attempt


def final_grade_from_attempts(quiz, attempts):
    graded_attempts = [attempt for attempt in attempts if attempt.score is not None]
    if not graded_attempts:
        return None, None
    if quiz.grade_method == Quiz.GRADE_FIRST:
        selected = graded_attempts[0]
        return selected.score, selected
    if quiz.grade_method == Quiz.GRADE_LAST:
        selected = graded_attempts[-1]
        return selected.score, selected
    if quiz.grade_method == Quiz.GRADE_AVERAGE:
        total = sum((attempt.score for attempt in graded_attempts), Decimal("0.00"))
        return (total / len(graded_attempts)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP), graded_attempts[-1]
    selected = max(graded_attempts, key=lambda item: item.score)
    return selected.score, selected


def recompute_quiz_grade(quiz, student):
    attempts = list(QuizAttempt.objects.filter(quiz=quiz, student=student).order_by("attempt_number"))
    grade, selected = final_grade_from_attempts(quiz, attempts)
    needs_manual = any(attempt.needs_manual_grading for attempt in attempts)
    record, _created = QuizGrade.objects.get_or_create(quiz=quiz, student=student)
    record.grade = grade
    record.best_attempt = selected
    record.attempts_count = len(attempts)
    record.needs_manual_grading = needs_manual
    record.save()
    from gradebook_app.services import sync_quiz_grade

    sync_quiz_grade(record)
    return record


@transaction.atomic
def submit_attempt(attempt, *, actor, ip_address="", responses=None):
    if attempt.state not in {QuizAttempt.STATE_IN_PROGRESS, QuizAttempt.STATE_OVERDUE}:
        raise QuizWorkflowError("This attempt has already been submitted.", status_code=409)
    responses = responses or {}
    for raw_id, response in responses.items():
        question_attempt = attempt.question_attempts.filter(pk=raw_id).first()
        if question_attempt:
            save_question_response(
                question_attempt,
                response,
                actor=actor,
                ip_address=ip_address,
                state=QuestionAttemptStep.STATE_SUBMITTED,
            )
    for question_attempt in attempt.question_attempts.select_related("question_version", "question_version__question").prefetch_related("question_version__choices"):
        grade_question_attempt(question_attempt)
        QuestionAttemptStep.objects.create(
            question_attempt=question_attempt,
            sequence_number=next_step_number(question_attempt),
            state=QuestionAttemptStep.STATE_SUBMITTED,
            response=question_attempt.response,
            fraction=(question_attempt.awarded_mark / question_attempt.max_mark) if question_attempt.max_mark else Decimal("0.0000"),
            actor=actor,
            ip_address=ip_address or None,
        )
    attempt.state = QuizAttempt.STATE_OVERDUE if attempt.due_at and timezone.now() > attempt.due_at else QuizAttempt.STATE_SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.submitted_ip = ip_address or None
    attempt.save(update_fields=["state", "submitted_at", "submitted_ip", "updated_at"])
    recompute_attempt_score(attempt)
    recompute_quiz_grade(attempt.quiz, attempt.student)
    return attempt


@transaction.atomic
def manually_grade_question(question_attempt, teacher, *, awarded_mark, feedback=""):
    max_mark = question_attempt.max_mark
    score = decimal_value(awarded_mark, default=0, minimum=0, maximum=max_mark)
    question_attempt.awarded_mark = score
    question_attempt.feedback = str(feedback or "").strip()
    question_attempt.requires_manual_grading = False
    question_attempt.manually_graded_by = teacher
    question_attempt.manually_graded_at = timezone.now()
    question_attempt.save(
        update_fields=[
            "awarded_mark",
            "feedback",
            "requires_manual_grading",
            "manually_graded_by",
            "manually_graded_at",
            "updated_at",
        ]
    )
    QuestionAttemptStep.objects.create(
        question_attempt=question_attempt,
        sequence_number=next_step_number(question_attempt),
        state=QuestionAttemptStep.STATE_GRADED,
        response=question_attempt.response,
        fraction=(score / max_mark) if max_mark else Decimal("0.0000"),
        actor=teacher,
    )
    recompute_attempt_score(question_attempt.attempt)
    recompute_quiz_grade(question_attempt.quiz, question_attempt.attempt.student)
    return question_attempt


def question_attempt_payload(question_attempt, *, review=False, teacher=False, in_progress=False):
    version = question_attempt.question_version
    include_answers = teacher or (review and question_attempt.attempt.quiz.review_show_right_answer)
    payload = {
        "id": question_attempt.id,
        "slot_number": question_attempt.slot_number,
        "max_mark": str(question_attempt.max_mark),
        "response": question_attempt.response,
        "response_summary": question_attempt.response_summary,
        "awarded_mark": (
            str(question_attempt.awarded_mark)
            if (teacher or question_attempt.attempt.quiz.review_show_marks) and question_attempt.awarded_mark is not None
            else None
        ),
        "requires_manual_grading": question_attempt.requires_manual_grading,
        "feedback": question_attempt.feedback if (teacher or question_attempt.attempt.quiz.review_show_feedback) else "",
        "right_answer_summary": question_attempt.right_answer_summary if include_answers else "",
        "question": question_version_payload(version, include_answers=include_answers),
    }
    if in_progress or teacher:
        payload["question"]["choices"] = question_version_payload(version, include_answers=include_answers)["choices"]
    return payload


def attempt_payload(attempt, *, include_questions=True, review=False, teacher=False):
    payload = {
        "id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "quiz_title": attempt.quiz.title,
        "student": profile_display_name(attempt.student),
        "student_id": attempt.student_id,
        "attempt_number": attempt.attempt_number,
        "state": attempt.state,
        "state_label": attempt.get_state_display(),
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "due_at": attempt.due_at.isoformat() if attempt.due_at else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "score": str(attempt.score) if attempt.score is not None else None,
        "needs_manual_grading": attempt.needs_manual_grading,
        "offering": offering_payload(attempt.quiz.offering),
        "review_allowed": attempt.state in {QuizAttempt.STATE_SUBMITTED, QuizAttempt.STATE_OVERDUE} and attempt.quiz.review_show_attempt,
    }
    if include_questions:
        payload["questions"] = [
            question_attempt_payload(
                question_attempt,
                review=review,
                teacher=teacher,
                in_progress=attempt.state == QuizAttempt.STATE_IN_PROGRESS,
            )
            for question_attempt in attempt.question_attempts.select_related(
                "question_version",
                "question_version__question",
            ).prefetch_related("question_version__choices")
        ]
    return payload


def teacher_options_payload(teacher):
    offerings = teacher_offerings(teacher)
    return {
        "offerings": [offering_payload(offering) for offering in offerings],
        "question_types": question_type_metadata(),
        "grade_methods": [{"value": value, "label": label} for value, label in Quiz.GRADE_CHOICES],
    }


def student_access_payload(quiz, student, *, ip_address="", safe_exam_browser_key=""):
    can_start, reason = start_access_status(
        quiz,
        student,
        password="",
        ip_address=ip_address,
        safe_exam_browser_key=safe_exam_browser_key,
    )
    if quiz.password and reason == "Quiz password is required or incorrect.":
        can_start = True
        reason = "Password required."
    if quiz.require_safe_exam_browser and reason == "Safe Exam Browser is required for this quiz.":
        can_start = False
    return {
        "can_start": can_start,
        "reason": reason,
        "password_required": bool(quiz.password),
        "safe_exam_browser_required": quiz.require_safe_exam_browser,
    }
