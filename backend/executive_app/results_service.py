from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from executive_app.course_schedule import (
    get_executive_profile,
    get_executive_scope,
    offerings_for_scope,
    scope_payload,
    scope_supports_academic_workflows,
)
from executive_app.models import (
    ResultApproval,
    ResultBatch,
    ResultPublication,
    ResultRecord,
    ResultReviewNote,
)
from notifications_package.service import notify_profile, notify_profiles
from student_app.models import Enrollment, TranscriptRecord
from teacher_app.assignment_service import (
    get_teacher_profile,
    profile_display_name,
    teacher_offerings,
)
from gradebook_app.services import grade_for_score as gradebook_grade_for_score


STATUS_LABELS = {
    "not_started": "Not started",
    "draft": "Draft",
    "review": "Under review",
    "approved": "Approved",
    "published": "Published",
}


class ResultWorkflowError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _decimal_score(value):
    if value in (None, ""):
        return None
    try:
        score = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise ResultWorkflowError("Scores must be valid numbers.")
    if score < 0 or score > 100:
        raise ResultWorkflowError("Scores must be between 0 and 100.")
    return score


def grade_for_score(score):
    if score is None:
        return "", None
    return gradebook_grade_for_score(score)


def _offering_payload(offering):
    return {
        "id": offering.id,
        "course_code": offering.course.code,
        "course_title": offering.course.title,
        "credits": str(offering.course.credits),
        "section": offering.section,
        "semester_id": offering.semester_id,
        "semester": offering.semester.name,
        "semester_active": offering.semester.is_active,
        "teacher": profile_display_name(offering.instructor),
    }


def _record_payload(record):
    return {
        "id": record.id,
        "student_id": record.student_id,
        "student_number": record.student.student_id,
        "student_name": profile_display_name(record.student),
        "score": str(record.score) if record.score is not None else "",
        "grade": record.grade,
        "grade_points": str(record.grade_points) if record.grade_points is not None else "",
        "remarks": record.remarks,
    }


def serialize_batch(batch, *, include_records=True):
    latest_note = batch.review_notes.order_by("-created_at").first()
    payload = {
        "id": batch.id,
        "status": batch.status,
        "status_label": STATUS_LABELS.get(batch.status, batch.status.title()),
        "offering": _offering_payload(batch.offering),
        "created_by": profile_display_name(batch.created_by),
        "record_count": batch.records.count(),
        "enrollment_count": Enrollment.objects.filter(
            offering=batch.offering,
            completed_at__isnull=True,
        ).count(),
        "submitted_at": batch.submitted_at.isoformat() if batch.submitted_at else None,
        "reviewed_at": batch.reviewed_at.isoformat() if batch.reviewed_at else None,
        "published_at": batch.published_at.isoformat() if batch.published_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
        "latest_review": {
            "status": latest_note.status,
            "note": latest_note.note,
            "author": profile_display_name(latest_note.author),
            "created_at": latest_note.created_at.isoformat(),
        }
        if latest_note
        else None,
    }
    if include_records:
        payload["records"] = [
            _record_payload(record)
            for record in batch.records.select_related("student", "student__user").order_by(
                "student__student_detail__student_id",
                "student__user__first_name",
                "student__user__last_name",
            )
        ]
    return payload


def _latest_batches_for_offerings(offerings):
    offering_ids = list(offerings.values_list("id", flat=True))
    batches = (
        ResultBatch.objects.select_related(
            "offering",
            "offering__course",
            "offering__semester",
            "offering__instructor",
            "offering__instructor__user",
            "created_by",
            "created_by__user",
        )
        .filter(offering_id__in=offering_ids)
        .order_by("offering_id", "-created_at", "-id")
    )
    latest = {}
    for batch in batches:
        latest.setdefault(batch.offering_id, batch)
    return latest


def _teacher_offering_rows(profile):
    offerings = teacher_offerings(profile, include_inactive=True)
    latest = _latest_batches_for_offerings(offerings)
    rows = []
    for offering in offerings:
        batch = latest.get(offering.id)
        rows.append(
            {
                **_offering_payload(offering),
                "student_count": Enrollment.objects.filter(
                    offering=offering,
                    completed_at__isnull=True,
                ).count(),
                "batch": serialize_batch(batch, include_records=False) if batch else None,
                "status": batch.status if batch else "not_started",
                "status_label": STATUS_LABELS.get(
                    batch.status if batch else "not_started",
                    "Not started",
                ),
            }
        )
    return rows


def _roster_payload(offering, batch):
    existing = {
        record.student_id: record
        for record in batch.records.select_related("student", "student__user")
    } if batch else {}
    enrollments = (
        Enrollment.objects.select_related("student", "student__user")
        .filter(offering=offering, completed_at__isnull=True)
        .order_by(
            "student__student_detail__student_id",
            "student__user__first_name",
            "student__user__last_name",
        )
    )
    rows = []
    for enrollment in enrollments:
        record = existing.get(enrollment.student_id)
        rows.append(
            {
                "student_id": enrollment.student_id,
                "student_number": enrollment.student.student_id,
                "student_name": profile_display_name(enrollment.student),
                "score": str(record.score) if record and record.score is not None else "",
                "grade": record.grade if record else "",
                "grade_points": (
                    str(record.grade_points)
                    if record and record.grade_points is not None
                    else ""
                ),
                "remarks": record.remarks if record else "",
            }
        )
    return rows


def teacher_results_payload(user, *, view="overview", offering_id=None):
    profile = get_teacher_profile(user)
    offerings = teacher_offerings(profile, include_inactive=True)
    offering_rows = _teacher_offering_rows(profile)
    allowed_statuses = {
        "draft": {"draft"},
        "completed": {"review", "approved", "published"},
    }.get(view)
    if allowed_statuses is not None:
        offering_rows = [
            row for row in offering_rows if row["status"] in allowed_statuses
        ]

    selected_offering = None
    selected_batch = None
    roster = []
    if view == "submit":
        selected_offering = (
            offerings.filter(pk=offering_id).first()
            if offering_id
            else offerings.filter(semester__is_active=True).first() or offerings.first()
        )
        if selected_offering:
            selected_batch = (
                ResultBatch.objects.select_related(
                    "offering",
                    "offering__course",
                    "offering__semester",
                    "offering__instructor",
                    "offering__instructor__user",
                    "created_by",
                    "created_by__user",
                )
                .filter(offering=selected_offering)
                .order_by("-created_at", "-id")
                .first()
            )
            roster = _roster_payload(selected_offering, selected_batch)

    status_counts = defaultdict(int)
    for row in _teacher_offering_rows(profile):
        status_counts[row["status"]] += 1
    return {
        "title": {
            "overview": "Results",
            "submit": "Submit Results",
            "draft": "Draft Results",
            "completed": "Completed Results",
        }.get(view, "Results"),
        "section": "teacher",
        "summary": {
            "offerings": sum(status_counts.values()),
            "not_started": status_counts["not_started"],
            "draft": status_counts["draft"],
            "review": status_counts["review"],
            "approved": status_counts["approved"],
            "published": status_counts["published"],
        },
        "offerings": offering_rows,
        "selected_offering": _offering_payload(selected_offering)
        if selected_offering
        else None,
        "selected_batch": serialize_batch(selected_batch)
        if selected_batch
        else None,
        "roster": roster,
    }


@transaction.atomic
def save_teacher_results(user, data):
    profile = get_teacher_profile(user)
    offering = teacher_offerings(profile, include_inactive=True).filter(
        pk=data.get("offering_id")
    ).first()
    if not offering:
        raise ResultWorkflowError("Course offering not found.", 404)

    batch = (
        ResultBatch.objects.select_for_update()
        .filter(offering=offering)
        .order_by("-created_at", "-id")
        .first()
    )
    if batch and batch.status in {"review", "approved", "published"}:
        raise ResultWorkflowError(
            "This batch is locked because it has already been submitted for review.",
            409,
        )
    if not batch:
        batch = ResultBatch.objects.create(offering=offering, created_by=profile)

    enrollments = {
        enrollment.student_id: enrollment
        for enrollment in Enrollment.objects.select_related("student").filter(
            offering=offering,
            completed_at__isnull=True,
        )
    }
    if not enrollments:
        raise ResultWorkflowError("This course offering has no enrolled students.")

    submitted_rows = data.get("records")
    if not isinstance(submitted_rows, list):
        raise ResultWorkflowError("A records list is required.")

    seen = set()
    for row in submitted_rows:
        try:
            student_id = int(row.get("student_id"))
        except (TypeError, ValueError):
            raise ResultWorkflowError("Each result row requires a valid student.")
        if student_id not in enrollments:
            raise ResultWorkflowError("A result row contains a student outside this course.")
        if student_id in seen:
            raise ResultWorkflowError("Each student can only appear once in a result batch.")
        seen.add(student_id)
        score = _decimal_score(row.get("score"))
        grade, grade_points = grade_for_score(score)
        ResultRecord.objects.update_or_create(
            batch=batch,
            student_id=student_id,
            defaults={
                "score": score,
                "grade": grade,
                "grade_points": grade_points,
                "remarks": str(row.get("remarks", "")).strip(),
            },
        )

    action = str(data.get("action", "save")).strip().lower()
    if action not in {"save", "submit"}:
        raise ResultWorkflowError("Action must be save or submit.")
    if action == "submit":
        records = list(batch.records.all())
        scored_students = {
            record.student_id for record in records if record.score is not None
        }
        missing = set(enrollments) - scored_students
        if missing:
            raise ResultWorkflowError(
                "Enter a score for every enrolled student before submitting."
            )
        batch.status = "review"
        batch.submitted_at = timezone.now()
        batch.reviewed_at = None
        message = "Results submitted for executive review."
    else:
        batch.status = "draft"
        message = "Result draft saved."
    batch.created_by = profile
    batch.save(
        update_fields=[
            "status",
            "submitted_at",
            "reviewed_at",
            "created_by",
            "updated_at",
        ]
    )
    return message, serialize_batch(batch)


def _executive_batches(scope):
    return ResultBatch.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
        "offering__instructor",
        "offering__instructor__user",
        "created_by",
        "created_by__user",
    ).filter(offering__in=offerings_for_scope(scope))


def executive_results_payload(user, *, view="overview"):
    profile = get_executive_profile(user)
    try:
        scope = get_executive_scope(profile)
        scope_error = None
    except ValueError as exc:
        scope = {"kind": None, "unit": None}
        scope_error = str(exc)

    if not scope_supports_academic_workflows(scope):
        batches = ResultBatch.objects.none()
        scope_error = scope_error or (
            "Assign this executive to a school or academic centre to manage results."
        )
    else:
        batches = _executive_batches(scope)

    if view == "semester":
        batches = batches.filter(offering__semester__is_active=True)
    elif view == "review":
        batches = batches.filter(status="review")
    elif view == "publication":
        batches = batches.filter(status="approved")
    elif view == "previous":
        batches = batches.filter(status="published")

    all_batches = _executive_batches(scope) if scope_supports_academic_workflows(scope) else ResultBatch.objects.none()
    counts = {
        "batches": all_batches.count(),
        "records": all_batches.aggregate(total=Count("records"))["total"] or 0,
    }
    for status_value in ("draft", "review", "approved", "published"):
        counts[status_value] = all_batches.filter(status=status_value).count()

    return {
        "title": {
            "overview": "Results",
            "semester": "Semester Results",
            "review": "Results Review",
            "publication": "Results Publication",
            "previous": "Previous Results",
        }.get(view, "Results"),
        "section": "executive",
        "scope": scope_payload(scope),
        "scope_error": scope_error,
        "summary": counts,
        "batches": [
            serialize_batch(batch)
            for batch in batches.order_by(
                "-offering__semester__start_date",
                "offering__course__code",
                "offering__section",
                "-created_at",
            )
        ],
    }


def _weighted_average(records):
    credits = Decimal("0")
    weighted = Decimal("0")
    for record in records:
        if record.grade_points is None:
            continue
        credit = Decimal(str(record.credit_hours or 0))
        credits += credit
        weighted += credit * record.grade_points
    if not credits:
        return Decimal("0.00")
    return (weighted / credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _recalculate_student_metrics(student_id):
    records = list(
        TranscriptRecord.objects.select_related("semester")
        .filter(student_id=student_id, published_at__isnull=False)
        .order_by("semester__start_date", "semester_id", "id")
    )
    grouped = defaultdict(list)
    semester_order = []
    for record in records:
        key = record.semester_id
        if key not in grouped:
            semester_order.append(key)
        grouped[key].append(record)

    cumulative = []
    changed = []
    for semester_id in semester_order:
        semester_records = grouped[semester_id]
        cumulative.extend(semester_records)
        gpa = _weighted_average(semester_records)
        cgpa = _weighted_average(cumulative)
        for record in semester_records:
            record.gpa = gpa
            record.cgpa = cgpa
            changed.append(record)
    if changed:
        TranscriptRecord.objects.bulk_update(changed, ["gpa", "cgpa"])


@transaction.atomic
def review_result_batch(user, data):
    profile = get_executive_profile(user)
    scope = get_executive_scope(profile)
    if not scope_supports_academic_workflows(scope):
        raise ResultWorkflowError(
            "This executive scope does not support academic result workflows.",
            403,
        )
    batch = (
        _executive_batches(scope)
        .select_for_update(of=("self",))
        .filter(pk=data.get("batch_id"))
        .first()
    )
    if not batch:
        raise ResultWorkflowError("Result batch not found in your scope.", 404)
    if batch.status != "review":
        raise ResultWorkflowError("Only batches under review can be reviewed.", 409)

    action = str(data.get("action", "")).strip().lower()
    note = str(data.get("note", "")).strip()
    if action == "approve":
        batch.status = "approved"
        ResultApproval.objects.create(
            batch=batch,
            approved_by=profile,
            note=note,
        )
        message = "Result batch approved."
    elif action == "return":
        if not note:
            raise ResultWorkflowError("Add a review note before returning results.")
        batch.status = "draft"
        message = "Result batch returned to the teacher."
    else:
        raise ResultWorkflowError("Action must be approve or return.")

    batch.reviewed_at = timezone.now()
    batch.save(update_fields=["status", "reviewed_at", "updated_at"])
    ResultReviewNote.objects.create(
        batch=batch,
        author=profile,
        status=batch.status,
        note=note or message,
    )
    notify_profile(
        batch.created_by,
        event_type=f"results.{batch.status}",
        verb=f"{batch.offering.course.code} results: {message}",
        actor=profile,
        data={"batch_id": batch.id, "offering_id": batch.offering_id},
        url="/teacher/results/completed" if batch.status == "approved" else "/teacher/results/draft",
    )
    return message, serialize_batch(batch)


@transaction.atomic
def publish_result_batch(user, data):
    profile = get_executive_profile(user)
    scope = get_executive_scope(profile)
    if not scope_supports_academic_workflows(scope):
        raise ResultWorkflowError(
            "This executive scope does not support academic result workflows.",
            403,
        )
    batch = (
        _executive_batches(scope)
        .select_for_update(of=("self",))
        .filter(pk=data.get("batch_id"))
        .first()
    )
    if not batch:
        raise ResultWorkflowError("Result batch not found in your scope.", 404)
    if batch.status != "approved":
        raise ResultWorkflowError("Only approved result batches can be published.", 409)

    now = timezone.now()
    affected_students = set()
    records = batch.records.select_related("student", "batch__offering__course")
    for record in records:
        TranscriptRecord.objects.update_or_create(
            student=record.student,
            offering=batch.offering,
            defaults={
                "semester": batch.offering.semester,
                "course_code": batch.offering.course.code,
                "course_title": batch.offering.course.title,
                "credit_hours": batch.offering.course.credits,
                "score": record.score,
                "grade": record.grade,
                "grade_points": record.grade_points,
                "published_at": now,
            },
        )
        affected_students.add(record.student_id)

    for student_id in affected_students:
        _recalculate_student_metrics(student_id)

    publication = ResultPublication.objects.filter(offering=batch.offering).order_by(
        "-published_at"
    ).first()
    if publication:
        publication.published_by = profile
        publication.notes = str(data.get("note", "")).strip()
        publication.published_at = now
        publication.save(update_fields=["published_by", "notes", "published_at"])
    else:
        ResultPublication.objects.create(
            offering=batch.offering,
            published_by=profile,
            notes=str(data.get("note", "")).strip(),
        )

    batch.status = "published"
    batch.published_at = now
    batch.save(update_fields=["status", "published_at", "updated_at"])
    ResultReviewNote.objects.create(
        batch=batch,
        author=profile,
        status="published",
        note=str(data.get("note", "")).strip() or "Results published.",
    )

    recipients = list(
        Enrollment.objects.filter(offering=batch.offering).values_list(
            "student_id",
            flat=True,
        )
    )
    notify_profiles(
        recipients,
        event_type="results.published",
        verb=f"{batch.offering.course.code} results are now available.",
        actor=profile,
        data={"batch_id": batch.id, "offering_id": batch.offering_id},
        url="/student/results/semester",
    )
    notify_profile(
        batch.created_by,
        event_type="results.published",
        verb=f"{batch.offering.course.code} results were published.",
        actor=profile,
        data={"batch_id": batch.id, "offering_id": batch.offering_id},
        url="/teacher/results/completed",
    )
    return "Results published to student records.", serialize_batch(batch)
