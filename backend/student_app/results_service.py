from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from io import BytesIO
from pathlib import Path
from textwrap import wrap

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

from admin_app import models as admin_models
from admin_app.settings_registry import (
    institution_identity,
    institution_name,
    institution_short_name,
    terminology_settings,
)
from core.common.academic_policy import academic_standing_label, result_policy_labels
from gradebook_app.services import active_scale, grade_for_score as gradebook_grade_for_score
from student_app.models import Enrollment, Exam, ExamSlip, TranscriptRecord
from student_app.registration_service import active_semester, get_student_profile


FAIL_GRADES = {"C-", "D+", "D", "F"}
DEFAULT_COURSEWORK_WEIGHT = Decimal("60.00")
DEFAULT_FINAL_WEIGHT = Decimal("40.00")


def grade_scale_payload():
    return [
        {
            "grade": row.letter,
            "score": f"{_format_decimal(row.min_score)}-{_format_decimal(row.max_score)}",
            "points": _format_decimal(row.grade_points),
            "assessment": row.outcome,
        }
        for row in active_scale().ranges.all().order_by("-min_score", "sort_order")
    ]


def result_labels_payload():
    return result_policy_labels()


def _decimal(value, default=Decimal("0.00")):
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _format_decimal(value, places=2):
    value = _decimal(value)
    quant = Decimal("1") if places == 0 else Decimal(f"0.{'0' * (places - 1)}1")
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def _format_number(value, places=1):
    return _format_decimal(value, places=places)


def _grade_from_score(score):
    if score in (None, ""):
        return "", None
    return gradebook_grade_for_score(score)


def _is_failed(grade, grade_points):
    if grade in FAIL_GRADES:
        return True
    if grade_points is None:
        return False
    return _decimal(grade_points) < Decimal("2.00")


def _profile_name(profile):
    user = profile.user
    return (f"{user.first_name} {user.last_name}".strip() or user.username).upper()


def _student_identity(student, records=None):
    detail = getattr(student, "student_detail", None)
    program = getattr(student, "program", None)
    school = getattr(student, "school", None)
    records = records or []
    first_semester = next((record.semester for record in records if record.semester_id), None)
    program_label = ""
    if program:
        program_label = f"{program.code} - {program.name}" if program.code else program.name
    return {
        "name": _profile_name(student),
        "student_id": student.student_id or "",
        "identity_card_no": getattr(detail, "admission_number", "") or "",
        "school": school.name.upper() if school else "",
        "programme": program_label.upper(),
        "address": "",
        "intake_session": first_semester.name if first_semester else "",
    }


def _semester_payload(semester):
    if not semester:
        return {
            "id": "unassigned",
            "name": "Unassigned semester",
            "academic_session": "",
            "label": "Unassigned semester",
        }
    label = semester.name
    if semester.academic_session and semester.academic_session not in label:
        label = f"{label} ({semester.academic_session})"
    return {
        "id": str(semester.id),
        "name": semester.name,
        "academic_session": semester.academic_session,
        "label": label,
        "start_date": semester.start_date.isoformat() if semester.start_date else None,
        "end_date": semester.end_date.isoformat() if semester.end_date else None,
    }


def _course_code(record):
    if record.course_code:
        return record.course_code
    if record.offering_id and record.offering.course_id:
        return record.offering.course.code
    return ""


def _course_title(record):
    if record.course_title:
        return record.course_title
    if record.offering_id and record.offering.course_id:
        return record.offering.course.title
    return ""


def _credit_hours(record):
    if record.credit_hours:
        return _decimal(record.credit_hours)
    if record.offering_id and record.offering.course_id:
        return _decimal(record.offering.course.credits)
    return Decimal("0.00")


def published_transcript_records(student):
    if not student:
        return []
    return list(
        TranscriptRecord.objects.select_related(
            "semester",
            "offering",
            "offering__course",
            "student",
            "student__user",
            "student__student_detail",
            "student__student_detail__school",
            "student__student_detail__program",
        )
        .filter(student=student, published_at__isnull=False)
        .order_by("semester__start_date", "semester__id", "course_code", "id")
    )


def _annotated_records(records):
    annotated = []
    seen_codes = set()
    for record in sorted(
        records,
        key=lambda item: (
            item.semester.start_date if item.semester_id and item.semester.start_date else date.min,
            item.semester_id or 0,
            item.id,
        ),
    ):
        grade = record.grade
        grade_points = record.grade_points
        if not grade:
            grade, grade_points = _grade_from_score(record.score)
        code = _course_code(record)
        is_retake = bool(code and code in seen_codes)
        is_failed = _is_failed(grade, grade_points)
        note = ""
        if is_retake and is_failed:
            note = "Retake & Failed"
        elif is_retake:
            note = "Retake"
        elif is_failed:
            note = "Failed"
        if code:
            seen_codes.add(code)
        annotated.append(
            {
                "id": record.id,
                "semester_id": str(record.semester_id) if record.semester_id else "unassigned",
                "course_code": code,
                "course_title": _course_title(record),
                "credit_hours": _format_number(_credit_hours(record)),
                "score": _format_decimal(record.score) if record.score is not None else "",
                "grade": grade,
                "grade_points": _format_decimal(grade_points) if grade_points is not None else "",
                "gpa": _format_decimal(record.gpa) if record.gpa is not None else "",
                "cgpa": _format_decimal(record.cgpa) if record.cgpa is not None else "",
                "note": note,
                "published_at": record.published_at.isoformat() if record.published_at else None,
            }
        )
    return annotated


def _weighted_average(rows):
    credits = Decimal("0.00")
    weighted = Decimal("0.00")
    for row in rows:
        credit = _decimal(row.get("credit_hours"))
        points = _decimal(row.get("grade_points"), default=None)
        if points is None:
            continue
        credits += credit
        weighted += credit * points
    if credits <= 0:
        return Decimal("0.00")
    return (weighted / credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _latest_metric(rows, key):
    for row in reversed(rows):
        value = row.get(key)
        if value not in (None, ""):
            return _decimal(value)
    return None


def _summary(selected_rows, cumulative_rows, include_gpa=True):
    registered = sum((_decimal(row["credit_hours"]) for row in selected_rows), Decimal("0.00"))
    cumulative = sum((_decimal(row["credit_hours"]) for row in cumulative_rows), Decimal("0.00"))
    gpa = _latest_metric(selected_rows, "gpa") or _weighted_average(selected_rows)
    cgpa = _latest_metric(cumulative_rows, "cgpa") or _weighted_average(cumulative_rows)
    return {
        "include_gpa": include_gpa,
        "gpa": _format_decimal(gpa),
        "cgpa": _format_decimal(cgpa),
        "registered_unit": _format_number(registered),
        "counted_credit": _format_number(registered),
        "cumulative_credit_earned": _format_number(cumulative),
        "academic_status": academic_standing_label(cgpa),
    }


def _semester_options(records):
    seen = {}
    for record in records:
        key = str(record.semester_id) if record.semester_id else "unassigned"
        if key not in seen:
            seen[key] = _semester_payload(record.semester)
    return list(seen.values())


def _records_for_selected(annotated, selected):
    if selected == "all":
        return annotated
    return [row for row in annotated if row["semester_id"] == selected]


def _cumulative_rows_for_selected(annotated, semesters, selected):
    if selected == "all":
        return annotated
    order = [semester["id"] for semester in semesters]
    if selected not in order:
        return []
    allowed = set(order[: order.index(selected) + 1])
    return [row for row in annotated if row["semester_id"] in allowed]


def _group_rows(rows, semesters):
    labels = {semester["id"]: semester for semester in semesters}
    groups = []
    for semester in semesters:
        semester_rows = [row for row in rows if row["semester_id"] == semester["id"]]
        if semester_rows:
            groups.append({"semester": semester, "records": semester_rows})
    unknown_rows = [row for row in rows if row["semester_id"] not in labels]
    if unknown_rows:
        groups.append({"semester": _semester_payload(None), "records": unknown_rows})
    return groups


def semester_results_payload(request):
    student = get_student_profile(request.user)
    records = published_transcript_records(student)
    annotated = _annotated_records(records)
    semesters = _semester_options(records)
    selected = str(request.query_params.get("semester") or "all")
    if selected != "all" and selected not in {semester["id"] for semester in semesters}:
        selected = "all"
    selected_rows = _records_for_selected(annotated, selected)
    cumulative_rows = _cumulative_rows_for_selected(annotated, semesters, selected)
    return {
        "title": "Semester Results",
        "section": "student",
        "student": _student_identity(student, records),
        "semesters": [{"id": "all", "label": "All published results"}] + semesters,
        "selected_semester": selected,
        "groups": _group_rows(selected_rows, semesters),
        "records": selected_rows,
        "summary": _summary(selected_rows, cumulative_rows, include_gpa=selected != "all"),
        "grade_scale": grade_scale_payload(),
        "result_labels": result_labels_payload(),
    }


def transcript_payload(request):
    student = get_student_profile(request.user)
    records = published_transcript_records(student)
    annotated = _annotated_records(records)
    semesters = _semester_options(records)
    return {
        "title": "Transcript",
        "section": "student",
        "student": _student_identity(student, records),
        "semesters": semesters,
        "groups": _group_rows(annotated, semesters),
        "records": annotated,
        "summary": _summary(annotated, annotated, include_gpa=False),
        "grade_scale": grade_scale_payload(),
        "result_labels": result_labels_payload(),
    }


def _ratio_from_remarks(remarks):
    if not remarks:
        return DEFAULT_COURSEWORK_WEIGHT, DEFAULT_FINAL_WEIGHT
    text = str(remarks)
    for token in ("coursework_weight", "coursework"):
        marker = f"{token}="
        if marker in text:
            raw = text.split(marker, 1)[1].split()[0].strip("%,;")
            weight = _decimal(raw, DEFAULT_COURSEWORK_WEIGHT)
            if Decimal("0.00") <= weight <= Decimal("100.00"):
                return weight, Decimal("100.00") - weight
    return DEFAULT_COURSEWORK_WEIGHT, DEFAULT_FINAL_WEIGHT


def _ratio_from_offering(offering, fallback_remarks=""):
    if offering:
        coursework = _decimal(getattr(offering, "coursework_percentage", DEFAULT_COURSEWORK_WEIGHT))
        final = (
            _decimal(getattr(offering, "final_exam_percentage", DEFAULT_FINAL_WEIGHT))
            if getattr(offering, "has_final_exam", True)
            else Decimal("0.00")
        )
        return coursework, final
    return _ratio_from_remarks(fallback_remarks)


def courseworks_payload(request):
    from teacher_app.models import ResultSubmission

    student = get_student_profile(request.user)
    semester = active_semester(student=student)
    enrollments = []
    if student and semester:
        enrollments = list(
            Enrollment.objects.select_related(
                "offering",
                "offering__course",
                "offering__semester",
                "offering__instructor",
                "offering__instructor__user",
            )
            .filter(student=student, offering__semester=semester, completed_at__isnull=True)
            .order_by("offering__course__code", "offering__section")
        )
    submissions = {
        submission.offering_id: submission
        for submission in ResultSubmission.objects.filter(
            student=student,
            offering_id__in=[enrollment.offering_id for enrollment in enrollments],
        ).select_related("offering")
    }
    final_exams = {
        exam.offering_id: exam
        for exam in Exam.objects.filter(
            offering_id__in=[enrollment.offering_id for enrollment in enrollments],
            offering__has_final_exam=True,
            exam_type=Exam.TYPE_FINAL,
            is_published=True,
        ).select_related("offering")
    }
    transcript_codes = {row["course_code"]: row for row in _annotated_records(published_transcript_records(student))}
    rows = []
    for enrollment in enrollments:
        offering = enrollment.offering
        submission = submissions.get(offering.id)
        exam = final_exams.get(offering.id) if offering.has_final_exam else None
        coursework_weight, final_weight = _ratio_from_offering(
            offering,
            submission.remarks if submission else "",
        )
        course_code = offering.course.code
        previous = transcript_codes.get(course_code)
        note = "Retake" if previous and previous.get("note") in {"Failed", "Retake & Failed"} else ""
        rows.append(
            {
                "offering_id": offering.id,
                "course_code": course_code,
                "course_title": offering.course.title,
                "section": offering.section,
                "credit_hours": _format_number(offering.course.credits),
                "coursework_mark": _format_decimal(submission.score) if submission and submission.score is not None else "",
                "coursework_weight": _format_decimal(coursework_weight),
                "final_exam_weight": _format_decimal(final_weight),
                "has_final_exam": offering.has_final_exam,
                "status": "Published" if submission and submission.score is not None else "Pending",
                "published_at": submission.submitted_at.isoformat() if submission else None,
                "teacher": _profile_name(offering.instructor) if offering.instructor_id else "",
                "final_exam_starts_at": exam.starts_at.isoformat() if exam else None,
                "note": note,
            }
        )
    return {
        "title": "Course Works",
        "section": "student",
        "student": _student_identity(student),
        "semester": _semester_payload(semester) if semester else None,
        "default_coursework_weight": _format_decimal(DEFAULT_COURSEWORK_WEIGHT),
        "default_final_exam_weight": _format_decimal(DEFAULT_FINAL_WEIGHT),
        "courseworks": rows,
    }


def exam_slip_payload(request):
    student = get_student_profile(request.user)
    semester_id = request.query_params.get("semester")
    enrollments = Enrollment.objects.none()
    if student:
        enrollments = Enrollment.objects.select_related("offering", "offering__course", "offering__semester").filter(
            student=student,
            completed_at__isnull=True,
        )
    exams = (
        Exam.objects.select_related("semester", "offering", "offering__course")
        .prefetch_related("venue_allocations__venue__building")
        .filter(
            exam_type=Exam.TYPE_FINAL,
            is_published=True,
            offering__has_final_exam=True,
            offering_id__in=enrollments.values_list("offering_id", flat=True),
        )
        .order_by("starts_at", "offering__course__code")
    )
    if semester_id:
        exams = exams.filter(semester_id=semester_id)
    exams = list(exams)
    semesters = []
    seen_semesters = set()
    for exam in exams:
        if exam.semester_id not in seen_semesters:
            seen_semesters.add(exam.semester_id)
            semesters.append(_semester_payload(exam.semester))
    slip = None
    if student and exams:
        slip = (
            ExamSlip.objects.filter(student=student, semester=exams[0].semester, is_visible=True)
            .order_by("-updated_at")
            .first()
        )
    rows = [_exam_row(exam, student, index) for index, exam in enumerate(exams, start=1)]
    total_credits = sum((_decimal(row["credit_hours"]) for row in rows), Decimal("0.00"))
    return {
        "title": "Exam Slip",
        "section": "student",
        "student": _student_identity(student),
        "semester": _semester_payload(exams[0].semester) if exams else None,
        "semesters": semesters,
        "exams": rows,
        "total_credit_hours": _format_number(total_credits, places=0),
        "can_download": bool(rows),
        "generated_at": slip.generated_at.isoformat() if slip else timezone.now().isoformat(),
    }


def _exam_row(exam, student, index):
    venues = []
    seat_total = 0
    for allocation in exam.venue_allocations.all():
        seat_total += allocation.seats
        venue = allocation.venue
        parts = [venue.building.name if venue.building_id else "", venue.name]
        venues.append(", ".join(part for part in parts if part))
    table_no = ""
    if seat_total and student:
        table_no = str(((student.id * 17) + (exam.id * 7)) % seat_total + 1)
    return {
        "no": index,
        "course_code": exam.offering.course.code,
        "course_title": exam.offering.course.title,
        "credit_hours": _format_number(exam.offering.course.credits, places=0),
        "exam_date": timezone.localtime(exam.starts_at).strftime("%d %B,%Y"),
        "time": (
            f"{timezone.localtime(exam.starts_at).strftime('%-I.%M %p')} to "
            f"{timezone.localtime(exam.ends_at).strftime('%-I.%M %p') if exam.ends_at else ''}"
        ),
        "venue": " / ".join(venues),
        "note": "",
        "table_no": table_no,
    }


def pdf_response(filename, content):
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def result_pdf_response(request):
    payload = semester_results_payload(request)
    selected = payload["selected_semester"]
    filename = f"semester-results-{selected}.pdf"
    return pdf_response(filename, build_result_pdf(payload))


def exam_slip_pdf_response(request):
    payload = exam_slip_payload(request)
    return pdf_response("exam-slip.pdf", build_exam_slip_pdf(payload))


def _logo_path():
    identity = institution_identity()
    logo_url = str(identity.get("logo_url") or "").strip()
    if not logo_url or not logo_url.startswith("/"):
        return None
    path = Path(settings.BASE_DIR).parent / "frontend" / "public" / logo_url.lstrip("/")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        return None
    return path if path.exists() else None


def _institution_address_lines():
    identity = institution_identity()
    raw_address = str(identity.get("address") or "").strip()
    return [line.strip() for line in raw_address.splitlines() if line.strip()]


def _terminology_label(name, default):
    value = str(terminology_settings().get(name) or "").strip()
    return value or default


def _draw_border_text(canvas, text):
    canvas.saveState()
    canvas.setFont("Helvetica", 3.8)
    repeated = f"{text} | " * 8
    canvas.drawString(0, 815, repeated)
    canvas.drawString(0, 10, repeated)
    canvas.restoreState()


def _draw_logo(canvas, x, y, size):
    path = _logo_path()
    if path:
        canvas.drawImage(str(path), x, y, width=size, height=size, preserveAspectRatio=True, mask="auto")
        return
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawCentredString(x + size / 2, y + size / 2, institution_short_name()[:16].upper())


def _draw_wrapped(canvas, text, x, y, width, font="Helvetica", size=9, leading=11, max_lines=3):
    canvas.setFont(font, size)
    text = str(text or "")
    chars = max(8, int(width / (size * 0.48)))
    lines = wrap(text, width=chars)[:max_lines] or [""]
    for offset, line in enumerate(lines):
        canvas.drawString(x, y - (offset * leading), line)
    return len(lines)


def _draw_result_header(canvas, payload):
    from reportlab.lib.pagesizes import A4

    configured_institution_name = institution_name().upper()
    _draw_border_text(canvas, f"{configured_institution_name} EXAMINATION RESULT")
    width, height = A4
    _draw_logo(canvas, 32, height - 132, 44)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(82, height - 95, configured_institution_name)
    canvas.drawString(82, height - 107, "ACADEMIC RECORDS OFFICE")
    for index, line in enumerate(_institution_address_lines()[:2]):
        canvas.drawString(82, height - 119 - (index * 12), line.upper())
    canvas.setFont("Helvetica", 8)
    canvas.drawString(315, height - 95, "Note:  1.  The Senate's approval dictates the outcome of the examination")
    canvas.drawString(338, height - 115, "2.  If there are any modifications to this statement, the Dean's Office must be")
    canvas.drawString(350, height - 126, "informed within 15 days following the release of the examination results.")
    canvas.setFont("Helvetica", 16)
    canvas.drawCentredString(width / 2, height - 180, "EXAMINATION")
    semester_label = "ALL PUBLISHED RESULTS"
    if payload["selected_semester"] != "all" and payload["groups"]:
        semester = payload["groups"][0]["semester"]
        semester_label = f"{semester['name']}  ACADEMIC SESSION  {semester.get('academic_session') or ''}".strip()
    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(width / 2, height - 200, semester_label.upper())
    student = payload["student"]
    student_id_label = _terminology_label("student_id_label", "Student ID").upper()
    school_label = _terminology_label("school_label", "School").upper()
    program_label = _terminology_label("program_label", "Program").upper()
    y = height - 240
    pairs = [
        ("NAME", student["name"], f"{student_id_label} NO.", student["student_id"]),
        ("IDENTITY\nCARD NO.", student["identity_card_no"], school_label, student["school"]),
        ("ADDRESS", student["address"], f"ACADEMIC\n{program_label}", student["programme"]),
        ("", "", "DATE OF RESULT", timezone.localdate().strftime("%d-%m-%Y")),
    ]
    for left_label, left_value, right_label, right_value in pairs:
        if left_label:
            _draw_wrapped(canvas, left_label, 34, y, 48, size=9, leading=10)
            canvas.drawString(82, y, ":")
            _draw_wrapped(canvas, left_value, 96, y, 200, size=9, leading=10)
        if right_label:
            _draw_wrapped(canvas, right_label, 315, y, 90, size=9, leading=10)
            canvas.drawString(410, y, ":")
            _draw_wrapped(canvas, right_value, 424, y, 145, size=9, leading=10)
        y -= 30


def _draw_grid_table(canvas, x, y, columns, rows, font_size=8, header_height=26, row_height=20):
    canvas.setLineWidth(0.8)
    total_width = sum(width for _label, width in columns)
    canvas.rect(x, y - header_height, total_width, header_height, stroke=1, fill=0)
    cursor = x
    for label, width in columns:
        canvas.line(cursor, y, cursor, y - header_height)
        _draw_wrapped(canvas, label, cursor + 3, y - 9, width - 6, font="Helvetica-Bold", size=font_size, leading=9)
        cursor += width
    canvas.line(cursor, y, cursor, y - header_height)
    y -= header_height
    for row in rows:
        canvas.rect(x, y - row_height, total_width, row_height, stroke=1, fill=0)
        cursor = x
        for key, width in columns:
            canvas.line(cursor, y, cursor, y - row_height)
            _draw_wrapped(canvas, row.get(key, ""), cursor + 3, y - 12, width - 6, size=font_size, leading=8)
            cursor += width
        canvas.line(cursor, y, cursor, y - row_height)
        y -= row_height
    return y


def build_result_pdf(payload):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as reportlab_canvas

    buffer = BytesIO()
    pdf = reportlab_canvas.Canvas(buffer, pagesize=A4)
    _draw_result_header(pdf, payload)
    rows = []
    no = 1
    for group in payload["groups"]:
        for record in group["records"]:
            rows.append(
                {
                    "NO": str(no),
                    "COURSE\nCODE": record["course_code"],
                    "COURSE NAME": record["course_title"],
                    "GRADE": record["grade"],
                    "CREDIT\nHOUR": record["credit_hours"],
                    "NOTE": record["note"],
                }
            )
            no += 1
    y = _draw_grid_table(
        pdf,
        28,
        360,
        [
            ("NO", 32),
            ("COURSE\nCODE", 62),
            ("COURSE NAME", 255),
            ("GRADE", 52),
            ("CREDIT\nHOUR", 66),
            ("NOTE", 86),
        ],
        rows,
        font_size=9,
    )
    y -= 15
    summary = payload["summary"]
    labels = payload.get("result_labels") or result_labels_payload()
    pdf.rect(28, y - 78, 553, 78, stroke=1, fill=0)
    pdf.line(335, y, 335, y - 78)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(160, y - 35, "CUMULATIVE CREDIT")
    pdf.drawCentredString(160, y - 47, "EARNED")
    pdf.drawString(205, y - 41, ":")
    pdf.drawString(225, y - 41, summary["cumulative_credit_earned"])
    pdf.setFont("Helvetica", 9)
    if summary["include_gpa"]:
        pdf.drawString(360, y - 18, labels["gpa"])
        pdf.drawString(415, y - 18, summary["gpa"])
        pdf.drawString(475, y - 18, summary["registered_unit"])
        pdf.drawString(540, y - 18, summary["counted_credit"])
        pdf.drawString(360, y - 36, labels["cgpa"])
        pdf.drawString(415, y - 36, summary["cgpa"])
    else:
        pdf.drawString(360, y - 28, labels["cgpa"])
        pdf.drawString(415, y - 28, summary["cgpa"])
    pdf.drawString(400, y - 6, "AVERAGE")
    pdf.drawString(450, y - 6, "REGISTERED")
    pdf.drawString(520, y - 6, "COUNTED")
    pdf.drawString(404, y - 18 if summary["include_gpa"] else y - 28, "VALUE")
    pdf.drawString(463, y - 18 if summary["include_gpa"] else y - 28, "UNIT")
    pdf.drawString(523, y - 18 if summary["include_gpa"] else y - 28, "CREDIT")
    pdf.drawString(360, y - 56, "ACADEMIC")
    pdf.drawString(490, y - 56, summary["academic_status"])
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _draw_exam_slip_header(canvas, payload):
    from reportlab.lib.pagesizes import A4

    configured_institution_name = institution_name().upper()
    _draw_border_text(canvas, f"{configured_institution_name} FINAL EXAMINATION ENTRY SLIP & SCHEDULE")
    width, height = A4
    _draw_logo(canvas, width / 2 - 33, height - 130, 66)
    canvas.setFont("Times-Roman", 8)
    canvas.drawCentredString(width / 2, height - 143, configured_institution_name)
    canvas.setFont("Helvetica", 16)
    canvas.drawCentredString(width / 2, height - 164, "FINAL EXAMINATION ENTRY SLIP & SCHEDULE")
    semester = payload.get("semester") or {}
    label = f"{semester.get('name', '')}  ACADEMIC SESSION {semester.get('academic_session', '')}".strip()
    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(width / 2, height - 184, label.upper())
    student = payload["student"]
    student_id_label = _terminology_label("student_id_label", "Student ID")
    program_label = _terminology_label("program_label", "Program")
    y = height - 235
    left = [
        ("Name", student["name"]),
        ("Intake Session", student["intake_session"]),
        (program_label, student["programme"]),
    ]
    right = [
        ("IC/Passport No.", student["identity_card_no"]),
        (f"{student_id_label} No.", student["student_id"]),
        ("Date Printed", timezone.localtime().strftime("%d-%m-%Y %H:%M")),
    ]
    for index, (label, value) in enumerate(left):
        yy = y - index * 25
        canvas.setFont("Helvetica", 10)
        canvas.drawString(38, yy, label)
        canvas.drawString(122, yy, ":")
        _draw_wrapped(canvas, value, 136, yy, 220, size=10, leading=11)
    for index, (label, value) in enumerate(right):
        yy = y - index * 25
        canvas.drawString(375, yy, label)
        canvas.drawString(465, yy, ":")
        _draw_wrapped(canvas, value, 480, yy, 90, size=10, leading=11)


def build_exam_slip_pdf(payload):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as reportlab_canvas

    buffer = BytesIO()
    pdf = reportlab_canvas.Canvas(buffer, pagesize=A4)
    _draw_exam_slip_header(pdf, payload)
    rows = [
        {
            "NO": str(row["no"]),
            "COURSE": row["course_code"],
            "COURSE TITLE": row["course_title"],
            "UNIT": row["credit_hours"],
            "EXAM DATE": row["exam_date"],
            "TIME": row["time"],
            "EXAM VENUE": row["venue"],
            "NOTE": row["note"],
            "TABLE NO": row["table_no"],
        }
        for row in payload["exams"]
    ]
    _draw_grid_table(
        pdf,
        28,
        500,
        [
            ("NO", 26),
            ("COURSE", 55),
            ("COURSE TITLE", 140),
            ("UNIT", 30),
            ("EXAM DATE", 86),
            ("TIME", 82),
            ("EXAM VENUE", 75),
            ("NOTE", 40),
            ("TABLE NO", 45),
        ],
        rows,
        font_size=7,
        header_height=16,
        row_height=25,
    )
    pdf.setFont("Helvetica", 11)
    pdf.drawRightString(535, 265, f"Total Credit Hours :     {payload['total_credit_hours']}")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(30, 245, "EXAMINATION RULES AND REGULATIONS FOR")
    student_id_label = _terminology_label("student_id_label", "Student ID")
    rules = [
        "1) Students must be appropriately attired according to the dress code stipulated by the Student Affairs Department. NO slippers/flip flops/caps are allowed.",
        f"2) Students should bring their {student_id_label} card and Final Examination Slip and/or Identity Card to sit for the Examination in every examination that they attend.",
        "3) Candidates are NOT allowed to bring into the Final Examination's Hall/Venue; any notes, reference books, dictionaries of any kind, booklets, diagrams or pieces of paper, or any electronic equipment and communication aids.",
        "4) Students are not allowed to receive any prohibited items from anyone while in the Final Examination session, EXCEPT those given by the invigilator(s).",
        "5) Students can bring bottled drinking water into the examination hall. However, the container must be transparent and placed under your desk.",
        "6) Students who wear jackets/sweaters/cardigans and headcovers are subjected to inspection by an invigilator at any time during the examination.",
        "7) Students are not allowed to enter the examination hall thirty (30) minutes before the examination session begins.",
    ]
    y = 230
    for rule in rules:
        used = _draw_wrapped(pdf, rule, 30, y, 535, size=7.2, leading=10, max_lines=3)
        y -= max(1, used) * 10
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(220, 55, "---------------------------")
    pdf.drawCentredString(220, 42, "Student's signature")
    pdf.drawCentredString(395, 55, "----------------")
    pdf.drawCentredString(395, 42, "Date")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
