from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from admin_app.models import CourseOffering, Profile
from student_app.models import Enrollment
from student_app.registration_service import get_student_profile
from teacher_app.assignment_service import (
    get_teacher_profile,
    profile_display_name,
    teacher_offerings,
)

from gradebook_app.models import (
    GradebookCategory,
    GradebookGrade,
    GradebookGradeHistory,
    GradebookItem,
    GradebookScale,
    GradebookScaleRange,
)


SCORE_QUANT = Decimal("0.01")

DEFAULT_SCALE_ROWS = [
    {"letter": "A+", "min_score": "90", "max_score": "100", "grade_points": "4.00", "outcome": "High Distinction", "is_passing": True},
    {"letter": "A", "min_score": "80", "max_score": "89.99", "grade_points": "4.00", "outcome": "Distinction", "is_passing": True},
    {"letter": "A-", "min_score": "75", "max_score": "79.99", "grade_points": "3.67", "outcome": "High Credit", "is_passing": True},
    {"letter": "B+", "min_score": "70", "max_score": "74.99", "grade_points": "3.33", "outcome": "Credit", "is_passing": True},
    {"letter": "B", "min_score": "65", "max_score": "69.99", "grade_points": "3.00", "outcome": "Credit", "is_passing": True},
    {"letter": "B-", "min_score": "60", "max_score": "64.99", "grade_points": "2.67", "outcome": "Pass", "is_passing": True},
    {"letter": "C+", "min_score": "55", "max_score": "59.99", "grade_points": "2.33", "outcome": "Pass", "is_passing": True},
    {"letter": "C", "min_score": "50", "max_score": "54.99", "grade_points": "2.00", "outcome": "Pass", "is_passing": True},
    {"letter": "C-", "min_score": "40", "max_score": "49.99", "grade_points": "1.67", "outcome": "Fail", "is_passing": False},
    {"letter": "D+", "min_score": "35", "max_score": "39.99", "grade_points": "1.33", "outcome": "Fail", "is_passing": False},
    {"letter": "D", "min_score": "30", "max_score": "34.99", "grade_points": "1.00", "outcome": "Fail", "is_passing": False},
    {"letter": "F", "min_score": "0", "max_score": "29.99", "grade_points": "0.00", "outcome": "Fail", "is_passing": False},
]


class GradebookWorkflowError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def decimal_value(value, default=None, *, minimum=None, maximum=None):
    if value in (None, ""):
        if default is None:
            return None
        return Decimal(str(default)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    try:
        parsed = Decimal(str(value)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise GradebookWorkflowError("Scores and weights must be valid numbers.")
    if minimum is not None and parsed < Decimal(str(minimum)):
        raise GradebookWorkflowError(f"Value must be at least {minimum}.")
    if maximum is not None and parsed > Decimal(str(maximum)):
        raise GradebookWorkflowError(f"Value must be at most {maximum}.")
    return parsed


def bool_value(value, default=False):
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _format_decimal(value):
    if value in (None, ""):
        return ""
    return str(Decimal(str(value)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP))


def _profile_payload(profile):
    return {
        "id": profile.id,
        "name": profile_display_name(profile),
        "username": profile.user.username,
        "student_number": getattr(profile, "student_id", ""),
    }


def offering_payload(offering):
    return {
        "id": offering.id,
        "course_code": offering.course.code,
        "course_title": offering.course.title,
        "section": offering.section,
        "semester": offering.semester.name,
        "semester_active": offering.semester.is_active,
        "teacher": profile_display_name(offering.instructor),
    }


@transaction.atomic
def ensure_default_scale(created_by=None):
    scale = (
        GradebookScale.objects.select_for_update()
        .prefetch_related("ranges")
        .filter(is_default=True, is_active=True)
        .first()
    )
    if not scale:
        scale, _created = GradebookScale.objects.select_for_update().get_or_create(
            name="UMS Default Letter Scale",
            defaults={
                "description": "Default UMS letter scale. Admins can edit or replace it.",
                "is_active": True,
                "is_default": True,
                "created_by": created_by,
                "updated_by": created_by,
            },
        )
        GradebookScale.objects.exclude(pk=scale.pk).update(is_default=False)
        if not scale.is_default:
            scale.is_default = True
            scale.is_active = True
            scale.updated_by = created_by
            scale.save(update_fields=["is_default", "is_active", "updated_by", "updated_at"])

    if not scale.ranges.exists():
        GradebookScaleRange.objects.bulk_create(
            [
                GradebookScaleRange(
                    scale=scale,
                    letter=row["letter"],
                    min_score=Decimal(row["min_score"]),
                    max_score=Decimal(row["max_score"]),
                    grade_points=Decimal(row["grade_points"]),
                    outcome=row["outcome"],
                    is_passing=row["is_passing"],
                    sort_order=index,
                )
                for index, row in enumerate(DEFAULT_SCALE_ROWS, start=1)
            ]
        )
    return scale


def active_scale():
    scale = (
        GradebookScale.objects.prefetch_related("ranges")
        .filter(is_default=True, is_active=True)
        .first()
        or GradebookScale.objects.prefetch_related("ranges").filter(is_active=True).first()
    )
    return scale if scale and scale.ranges.exists() else ensure_default_scale()


def serialize_scale_range(row):
    return {
        "id": row.id,
        "letter": row.letter,
        "min_score": _format_decimal(row.min_score),
        "max_score": _format_decimal(row.max_score),
        "grade_points": _format_decimal(row.grade_points),
        "outcome": row.outcome,
        "is_passing": row.is_passing,
        "sort_order": row.sort_order,
    }


def serialize_scale(scale):
    ranges = list(scale.ranges.all().order_by("-min_score", "sort_order"))
    return {
        "id": scale.id,
        "name": scale.name,
        "description": scale.description,
        "is_active": scale.is_active,
        "is_default": scale.is_default,
        "ranges": [serialize_scale_range(row) for row in ranges],
        "updated_at": scale.updated_at.isoformat() if scale.updated_at else None,
        "updated_by": profile_display_name(scale.updated_by),
    }


def grade_for_score(score, scale=None):
    if score in (None, ""):
        return "", None
    percent = decimal_value(score, minimum=0, maximum=100)
    scale = scale or active_scale()
    for row in scale.ranges.all().order_by("-min_score", "sort_order"):
        if row.min_score <= percent <= row.max_score:
            return row.letter, row.grade_points
    return "F", Decimal("0.00")


@transaction.atomic
def save_scale(profile, data):
    name = str(data.get("name") or "UMS Grade Scale").strip()
    if not name:
        raise GradebookWorkflowError("Scale name is required.")
    ranges = data.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise GradebookWorkflowError("At least one grade range is required.")

    scale_id = data.get("id")
    scale = GradebookScale.objects.filter(pk=scale_id).first() if scale_id else None
    if not scale:
        scale = GradebookScale(created_by=profile)
    scale.name = name
    scale.description = str(data.get("description") or "").strip()
    scale.is_active = bool_value(data.get("is_active"), True)
    scale.is_default = bool_value(data.get("is_default"), True)
    scale.updated_by = profile
    if scale.is_default:
        GradebookScale.objects.exclude(pk=scale.pk).update(is_default=False)
    scale.save()

    scale.ranges.all().delete()
    parsed = []
    for index, row in enumerate(ranges, start=1):
        parsed_row = GradebookScaleRange(
            scale=scale,
            letter=str(row.get("letter") or "").strip(),
            min_score=decimal_value(row.get("min_score"), minimum=0, maximum=100),
            max_score=decimal_value(row.get("max_score"), default=100, minimum=0, maximum=100),
            grade_points=decimal_value(row.get("grade_points"), default=0, minimum=0, maximum=4),
            outcome=str(row.get("outcome") or "").strip(),
            is_passing=bool_value(row.get("is_passing"), True),
            sort_order=int(row.get("sort_order") or index),
        )
        if not parsed_row.letter:
            raise GradebookWorkflowError("Every grade range requires a grade letter.")
        parsed_row.full_clean()
        parsed.append(parsed_row)
    GradebookScaleRange.objects.bulk_create(parsed)
    return serialize_scale(GradebookScale.objects.prefetch_related("ranges").get(pk=scale.pk))


def admin_gradebook_payload():
    ensure_default_scale()
    return {
        "title": "Gradebook Criteria",
        "section": "admin",
        "scales": [
            serialize_scale(scale)
            for scale in GradebookScale.objects.prefetch_related("ranges").order_by("-is_default", "name")
        ],
        "summary": {
            "scales": GradebookScale.objects.count(),
            "categories": GradebookCategory.objects.count(),
            "items": GradebookItem.objects.count(),
            "grades": GradebookGrade.objects.count(),
        },
    }


def _default_category(offering, title, created_by=None):
    category, _created = GradebookCategory.objects.get_or_create(
        offering=offering,
        title=title,
        defaults={"created_by": created_by, "release_to_students": True},
    )
    return category


def _record_history(grade, previous_score, previous_status, actor, source, reason=""):
    if previous_score == grade.raw_score and previous_status == grade.status:
        return
    GradebookGradeHistory.objects.create(
        grade=grade,
        previous_score=previous_score,
        new_score=grade.raw_score,
        previous_status=previous_status,
        new_status=grade.status,
        changed_by=actor,
        source=source,
        reason=reason,
    )


@transaction.atomic
def sync_assignment_grade(submission, actor=None):
    assignment = submission.assignment
    category = _default_category(assignment.offering, "Assignments", assignment.created_by)
    item, _created = GradebookItem.objects.update_or_create(
        source_app="teacher_app",
        source_model="Assignment",
        source_id=assignment.id,
        defaults={
            "offering": assignment.offering,
            "category": category,
            "scale": active_scale(),
            "title": assignment.title,
            "item_type": GradebookItem.TYPE_ASSIGNMENT,
            "max_score": assignment.max_score,
            "due_at": assignment.due_date,
            "release_to_students": True,
            "created_by": assignment.created_by,
        },
    )
    grade, _grade_created = GradebookGrade.objects.get_or_create(
        item=item,
        student=submission.student,
    )
    if grade.is_override:
        return grade

    previous_score = grade.raw_score
    previous_status = grade.status
    grade.raw_score = submission.grade
    grade.feedback = submission.feedback
    grade.status = (
        GradebookGrade.STATUS_RELEASED
        if submission.grade is not None
        else GradebookGrade.STATUS_DRAFT
    )
    grade.graded_by = submission.graded_by or actor
    grade.graded_at = submission.graded_at
    grade.released_at = timezone.now() if grade.status == GradebookGrade.STATUS_RELEASED else None
    grade.source_attempt = f"assignment_submission:{submission.id}"
    grade.save()
    _record_history(grade, previous_score, previous_status, actor or submission.graded_by, "assignment")
    return grade


@transaction.atomic
def sync_quiz_grade(quiz_grade, actor=None):
    quiz = quiz_grade.quiz
    category = _default_category(quiz.offering, "Quizzes", quiz.created_by)
    max_score = quiz.total_marks if quiz.total_marks and quiz.total_marks > 0 else Decimal("100.00")
    item, _created = GradebookItem.objects.update_or_create(
        source_app="quiz_app",
        source_model="Quiz",
        source_id=quiz.id,
        defaults={
            "offering": quiz.offering,
            "category": category,
            "scale": active_scale(),
            "title": quiz.title,
            "item_type": GradebookItem.TYPE_QUIZ,
            "max_score": max_score,
            "due_at": quiz.closes_at,
            "release_to_students": bool(quiz.review_show_marks),
            "created_by": quiz.created_by,
        },
    )
    grade, _grade_created = GradebookGrade.objects.get_or_create(
        item=item,
        student=quiz_grade.student,
    )
    if grade.is_override:
        return grade

    previous_score = grade.raw_score
    previous_status = grade.status
    grade.raw_score = quiz_grade.grade
    grade.feedback = "Manual grading pending." if quiz_grade.needs_manual_grading else ""
    grade.status = (
        GradebookGrade.STATUS_RELEASED
        if quiz_grade.grade is not None and quiz.review_show_marks and not quiz_grade.needs_manual_grading
        else GradebookGrade.STATUS_DRAFT
    )
    grade.graded_by = actor
    grade.graded_at = timezone.now() if quiz_grade.grade is not None else None
    grade.released_at = timezone.now() if grade.status == GradebookGrade.STATUS_RELEASED else None
    grade.source_attempt = f"quiz_grade:{quiz_grade.id}"
    grade.save()
    _record_history(grade, previous_score, previous_status, actor, "quiz")
    return grade


def sync_sources_for_offering(offering):
    from quiz_app.models import QuizGrade
    from teacher_app.models import AssignmentSubmission

    assignment_count = 0
    submissions = (
        AssignmentSubmission.objects.select_related(
            "assignment",
            "assignment__offering",
            "assignment__created_by",
            "student",
            "graded_by",
        )
        .filter(assignment__offering=offering, grade__isnull=False)
    )
    for submission in submissions:
        sync_assignment_grade(submission, actor=submission.graded_by)
        assignment_count += 1

    quiz_count = 0
    for quiz_grade in QuizGrade.objects.select_related("quiz", "quiz__offering", "quiz__created_by", "student").filter(
        quiz__offering=offering,
        grade__isnull=False,
    ):
        sync_quiz_grade(quiz_grade)
        quiz_count += 1

    return {"assignment_grades": assignment_count, "quiz_grades": quiz_count}


def _student_roster(offering):
    return [
        enrollment.student
        for enrollment in Enrollment.objects.select_related("student", "student__user", "student__student_detail")
        .filter(offering=offering, completed_at__isnull=True)
        .order_by("student__student_detail__student_id", "student__user__first_name", "student__user__last_name")
    ]


def _item_percent(item, grade, *, released_only=False):
    if released_only and not item.release_to_students:
        return None
    if grade and released_only and grade.status != GradebookGrade.STATUS_RELEASED:
        return None
    if grade and grade.status == GradebookGrade.STATUS_EXCUSED:
        return None
    raw_score = Decimal("0.00")
    if grade and grade.raw_score is not None and grade.status != GradebookGrade.STATUS_MISSING:
        raw_score = Decimal(str(grade.raw_score))
    if item.max_score <= 0:
        return None
    return ((raw_score / Decimal(str(item.max_score))) * Decimal("100")).quantize(
        SCORE_QUANT,
        rounding=ROUND_HALF_UP,
    )


def _aggregate_items(items, grades_by_item, student_id, *, released_only=False):
    included = []
    for item in items:
        grade = grades_by_item.get((item.id, student_id))
        percent = _item_percent(item, grade, released_only=released_only)
        if percent is not None:
            included.append((item, percent, grade))
    if not included:
        return None

    weighted = [(item, percent) for item, percent, _grade in included if item.weight > 0]
    if weighted:
        weight_total = sum((Decimal(str(item.weight)) for item, _percent in weighted), Decimal("0.00"))
        if weight_total > 0:
            total = sum((percent * Decimal(str(item.weight)) for item, percent in weighted), Decimal("0.00"))
            return (total / weight_total).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)

    max_total = sum((Decimal(str(item.max_score)) for item, _percent, grade in included if not grade or grade.status != GradebookGrade.STATUS_EXCUSED), Decimal("0.00"))
    if max_total <= 0:
        return None
    raw_total = sum(
        (
            Decimal(str(grade.raw_score))
            if grade and grade.raw_score is not None and grade.status != GradebookGrade.STATUS_MISSING
            else Decimal("0.00")
        )
        for _item, _percent, grade in included
    )
    return ((raw_total / max_total) * Decimal("100")).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)


def calculate_totals(offering, *, released_only=False):
    items = list(
        GradebookItem.objects.select_related("category", "scale")
        .filter(offering=offering, is_active=True, is_extra_credit=False)
        .order_by("category__sort_order", "sort_order", "title")
    )
    if released_only:
        items = [item for item in items if item.release_to_students]
    grades = list(GradebookGrade.objects.filter(item__in=items))
    grades_by_item = {(grade.item_id, grade.student_id): grade for grade in grades}
    students = _student_roster(offering)
    categories_by_id = {
        category.id: category
        for category in GradebookCategory.objects.filter(offering=offering, is_active=True)
    }
    items_by_category = defaultdict(list)
    for item in items:
        items_by_category[item.category_id].append(item)

    weighted_categories = [
        category
        for category in categories_by_id.values()
        if category.weight > 0 and items_by_category.get(category.id)
    ]
    category_weight_sum = sum((Decimal(str(category.weight)) for category in weighted_categories), Decimal("0.00"))
    totals = {}
    scale = active_scale()

    for student in students:
        if weighted_categories:
            weighted_total = Decimal("0.00")
            weight_total = Decimal("0.00")
            for category in weighted_categories:
                category_percent = _aggregate_items(
                    items_by_category[category.id],
                    grades_by_item,
                    student.id,
                    released_only=released_only,
                )
                if category_percent is None:
                    category_percent = Decimal("0.00")
                weight = Decimal(str(category.weight))
                weighted_total += category_percent * weight
                weight_total += weight

            uncategorized = items_by_category.get(None, [])
            remaining_weight = max(Decimal("0.00"), Decimal("100.00") - category_weight_sum)
            if uncategorized and remaining_weight > 0:
                category_percent = _aggregate_items(
                    uncategorized,
                    grades_by_item,
                    student.id,
                    released_only=released_only,
                )
                if category_percent is not None:
                    weighted_total += category_percent * remaining_weight
                    weight_total += remaining_weight
            score = (weighted_total / weight_total).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP) if weight_total else None
        else:
            score = _aggregate_items(items, grades_by_item, student.id, released_only=released_only)

        grade, points = grade_for_score(score, scale) if score is not None else ("", None)
        totals[student.id] = {
            "student_id": student.id,
            "score": _format_decimal(score),
            "grade": grade,
            "grade_points": _format_decimal(points),
        }
    return totals


def serialize_category(category):
    return {
        "id": category.id,
        "title": category.title,
        "weight": _format_decimal(category.weight),
        "drop_lowest": category.drop_lowest,
        "release_to_students": category.release_to_students,
        "is_active": category.is_active,
        "sort_order": category.sort_order,
    }


def serialize_item(item):
    return {
        "id": item.id,
        "category_id": item.category_id,
        "title": item.title,
        "item_type": item.item_type,
        "item_type_label": item.get_item_type_display(),
        "source_app": item.source_app,
        "source_model": item.source_model,
        "source_id": item.source_id,
        "max_score": _format_decimal(item.max_score),
        "weight": _format_decimal(item.weight),
        "due_at": item.due_at.isoformat() if item.due_at else None,
        "release_to_students": item.release_to_students,
        "is_extra_credit": item.is_extra_credit,
        "is_active": item.is_active,
        "sort_order": item.sort_order,
    }


def serialize_grade(grade):
    return {
        "id": grade.id,
        "item_id": grade.item_id,
        "student_id": grade.student_id,
        "raw_score": _format_decimal(grade.raw_score),
        "feedback": grade.feedback,
        "status": grade.status,
        "status_label": grade.get_status_display(),
        "is_override": grade.is_override,
        "graded_by": profile_display_name(grade.graded_by),
        "graded_at": grade.graded_at.isoformat() if grade.graded_at else None,
        "released_at": grade.released_at.isoformat() if grade.released_at else None,
    }


def gradebook_payload_for_offering(offering, *, released_only=False):
    categories = list(GradebookCategory.objects.filter(offering=offering).order_by("sort_order", "title"))
    items = list(
        GradebookItem.objects.select_related("category")
        .filter(offering=offering, is_active=True)
        .order_by("category__sort_order", "sort_order", "title")
    )
    if released_only:
        items = [item for item in items if item.release_to_students]
    grades = list(
        GradebookGrade.objects.select_related("student", "student__user", "graded_by", "graded_by__user")
        .filter(item__in=items)
        .order_by("item_id", "student__student_detail__student_id")
    )
    if released_only:
        grades = [grade for grade in grades if grade.status == GradebookGrade.STATUS_RELEASED]
    students = _student_roster(offering)
    totals = calculate_totals(offering, released_only=released_only)
    return {
        "offering": offering_payload(offering),
        "students": [_profile_payload(student) for student in students],
        "categories": [serialize_category(category) for category in categories],
        "items": [serialize_item(item) for item in items],
        "grades": [serialize_grade(grade) for grade in grades],
        "totals": [totals[student.id] for student in students if student.id in totals],
    }


def teacher_gradebook_payload(user, offering_id=None):
    profile = get_teacher_profile(user)
    offerings = teacher_offerings(profile, include_inactive=True)
    selected = offerings.filter(pk=offering_id).first() if offering_id else None
    if not selected:
        selected = offerings.filter(semester__is_active=True).first() or offerings.first()
    payload = {
        "title": "Gradebook",
        "section": "teacher",
        "offerings": [offering_payload(offering) for offering in offerings],
        "scale": serialize_scale(active_scale()),
        "selected": None,
    }
    if selected:
        payload["selected"] = gradebook_payload_for_offering(selected)
    return payload


def student_gradebook_payload(user):
    student = get_student_profile(user)
    enrollments = []
    if student:
        enrollments = list(
            Enrollment.objects.select_related("offering", "offering__course", "offering__semester", "offering__instructor", "offering__instructor__user")
            .filter(student=student, completed_at__isnull=True)
            .order_by("offering__course__code", "offering__section")
        )
    return {
        "title": "My Gradebook",
        "section": "student",
        "scale": serialize_scale(active_scale()),
        "courses": [
            gradebook_payload_for_offering(enrollment.offering, released_only=True)
            for enrollment in enrollments
        ],
    }


def _teacher_offering_or_error(user, offering_id):
    profile = get_teacher_profile(user)
    offering = teacher_offerings(profile, include_inactive=True).filter(pk=offering_id).first()
    if not offering:
        raise GradebookWorkflowError("Course offering not found for this teacher.", 404)
    return profile, offering


@transaction.atomic
def teacher_gradebook_action(user, data):
    action = str(data.get("action") or "").strip().lower()
    profile, offering = _teacher_offering_or_error(user, data.get("offering_id"))

    if action == "sync_sources":
        counts = sync_sources_for_offering(offering)
        return f"Synced {counts['assignment_grades']} assignment grades and {counts['quiz_grades']} quiz grades.", teacher_gradebook_payload(user, offering.id)

    if action == "save_category":
        category = GradebookCategory.objects.filter(pk=data.get("category_id"), offering=offering).first()
        if not category:
            category = GradebookCategory(offering=offering, created_by=profile)
        category.title = str(data.get("title") or "").strip()
        if not category.title:
            raise GradebookWorkflowError("Category title is required.")
        category.weight = decimal_value(data.get("weight"), default=0, minimum=0, maximum=100)
        category.drop_lowest = int(data.get("drop_lowest") or 0)
        category.release_to_students = bool_value(data.get("release_to_students"), False)
        category.is_active = bool_value(data.get("is_active"), True)
        category.sort_order = int(data.get("sort_order") or 0)
        category.full_clean()
        category.save()
        return "Gradebook category saved.", teacher_gradebook_payload(user, offering.id)

    if action == "save_item":
        item = GradebookItem.objects.filter(pk=data.get("item_id"), offering=offering).first()
        if not item:
            item = GradebookItem(offering=offering, created_by=profile)
        category = GradebookCategory.objects.filter(pk=data.get("category_id"), offering=offering).first()
        item.category = category
        item.scale = active_scale()
        item.title = str(data.get("title") or "").strip()
        if not item.title:
            raise GradebookWorkflowError("Grade item title is required.")
        item.item_type = data.get("item_type") if data.get("item_type") in {value for value, _label in GradebookItem.TYPE_CHOICES} else GradebookItem.TYPE_MANUAL
        item.max_score = decimal_value(data.get("max_score"), default=100, minimum=Decimal("0.01"))
        item.weight = decimal_value(data.get("weight"), default=0, minimum=0, maximum=100)
        item.release_to_students = bool_value(data.get("release_to_students"), False)
        item.is_extra_credit = bool_value(data.get("is_extra_credit"), False)
        item.is_active = bool_value(data.get("is_active"), True)
        item.sort_order = int(data.get("sort_order") or 0)
        item.full_clean()
        item.save()
        return "Gradebook item saved.", teacher_gradebook_payload(user, offering.id)

    if action == "update_grade":
        item = GradebookItem.objects.filter(pk=data.get("item_id"), offering=offering).first()
        if not item:
            raise GradebookWorkflowError("Grade item not found.", 404)
        student_ids = {student.id for student in _student_roster(offering)}
        try:
            student_id = int(data.get("student_id"))
        except (TypeError, ValueError):
            raise GradebookWorkflowError("A valid student is required.")
        if student_id not in student_ids:
            raise GradebookWorkflowError("Student is not enrolled in this course offering.", 403)
        grade, _created = GradebookGrade.objects.get_or_create(item=item, student_id=student_id)
        previous_score = grade.raw_score
        previous_status = grade.status
        grade.raw_score = decimal_value(data.get("raw_score"), minimum=0, maximum=item.max_score)
        grade.feedback = str(data.get("feedback") or "").strip()
        grade.status = data.get("status") if data.get("status") in {value for value, _label in GradebookGrade.STATUS_CHOICES} else GradebookGrade.STATUS_DRAFT
        grade.is_override = True
        grade.overridden_by = profile
        grade.graded_by = profile
        grade.graded_at = timezone.now()
        if grade.status == GradebookGrade.STATUS_RELEASED:
            grade.released_at = timezone.now()
        grade.full_clean()
        grade.save()
        _record_history(grade, previous_score, previous_status, profile, "manual", str(data.get("reason") or "").strip())
        return "Grade saved.", teacher_gradebook_payload(user, offering.id)

    if action == "release_item":
        item = GradebookItem.objects.filter(pk=data.get("item_id"), offering=offering).first()
        if not item:
            raise GradebookWorkflowError("Grade item not found.", 404)
        item.release_to_students = True
        item.save(update_fields=["release_to_students", "updated_at"])
        now = timezone.now()
        item.grades.exclude(status=GradebookGrade.STATUS_EXCUSED).update(
            status=GradebookGrade.STATUS_RELEASED,
            released_at=now,
        )
        return "Grade item released to students.", teacher_gradebook_payload(user, offering.id)

    if action == "send_to_result_draft":
        totals = calculate_totals(offering)
        if not GradebookItem.objects.filter(offering=offering, is_active=True).exists():
            raise GradebookWorkflowError("Create at least one gradebook item before sending totals to result draft.")
        records = [
            {"student_id": student_id, "score": row["score"], "remarks": "Copied from formative gradebook."}
            for student_id, row in totals.items()
            if row["score"] not in ("", None)
        ]
        if not records:
            raise GradebookWorkflowError("No gradebook totals are available for this course offering.")
        from executive_app.results_service import ResultWorkflowError, save_teacher_results

        try:
            message, _batch = save_teacher_results(
                user,
                {"offering_id": offering.id, "action": "save", "records": records},
            )
        except ResultWorkflowError as exc:
            raise GradebookWorkflowError(str(exc), exc.status_code)
        return f"{message} Gradebook totals were copied into the result draft.", teacher_gradebook_payload(user, offering.id)

    raise GradebookWorkflowError("Unsupported gradebook action.")
