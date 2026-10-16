from io import BytesIO
from textwrap import wrap

from django.http import HttpResponse
from django.utils.text import slugify

from accountant_app.ledger_service import student_finance_summary
from admin_app.settings_registry import portal_name
from admin_app.xlsx import build_xlsx


XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _filename(student, extension):
    identifier = student_finance_summary(student)["student"]["identifier"]
    stem = slugify(identifier) or f"student-{student.pk}"
    return f"student-ledger-{stem}.{extension}"


def _xlsx_content(summary):
    rows = [
        ["Student Ledger"],
        ["Portal", portal_name()],
        ["Student", summary["student"]["name"]],
        ["Identifier", summary["student"]["identifier"]],
        ["Email", summary["student"]["email"]],
        ["Current balance", summary["balance_display"]],
        [],
        ["Charges"],
        ["Category", "Description", "Amount", "Due date", "Status", "Created"],
    ]
    rows.extend(
        [
            charge["category"]["name"],
            charge["description"],
            charge["amount_display"],
            charge["due_date"] or "",
            charge["status"],
            charge["created_at"],
        ]
        for charge in summary["charges"]
    )
    rows.extend(
        [
            [],
            ["Ledger entries"],
            ["Posted", "Type", "Description", "Amount", "Balance after", "Posted by"],
        ]
    )
    rows.extend(
        [
            entry["posted_at"],
            entry["entry_type"],
            entry["description"],
            entry["amount_display"],
            entry["balance_after_display"],
            entry["posted_by"],
        ]
        for entry in summary["ledger_entries"]
    )
    return build_xlsx(rows, sheet_name="Student Ledger")


def _pdf_content(summary):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as reportlab_canvas

    buffer = BytesIO()
    pdf = reportlab_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 42

    def new_page():
        nonlocal y
        pdf.showPage()
        y = height - 42

    def line(text, *, bold=False, indent=0, leading=13):
        nonlocal y
        if y < 48:
            new_page()
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        pdf.drawString(36 + indent, y, str(text))
        y -= leading

    pdf.setTitle(f"Student ledger - {summary['student']['identifier']}")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(36, y, portal_name()[:70])
    y -= 21
    line("Student Ledger", bold=True, leading=18)
    line(f"Student: {summary['student']['name']}")
    line(f"Identifier: {summary['student']['identifier']}")
    line(f"Email: {summary['student']['email']}")
    line(f"Current balance: {summary['balance_display']}", bold=True, leading=20)

    line("Charges", bold=True, leading=16)
    if not summary["charges"]:
        line("No charges recorded.", indent=8)
    for charge in summary["charges"]:
        line(
            f"{charge['created_at'][:10]} | {charge['category']['code']} | "
            f"{charge['amount_display']} | {charge['status']}",
            bold=True,
            indent=8,
        )
        for description_line in wrap(charge["description"], width=88) or [""]:
            line(description_line, indent=16)

    y -= 7
    line("Ledger Entries", bold=True, leading=16)
    if not summary["ledger_entries"]:
        line("No ledger entries recorded.", indent=8)
    for entry in summary["ledger_entries"]:
        line(
            f"{entry['posted_at'][:10]} | {entry['entry_type']} | "
            f"{entry['amount_display']} | balance {entry['balance_after_display']}",
            bold=True,
            indent=8,
        )
        for description_line in wrap(entry["description"], width=88) or [""]:
            line(description_line, indent=16)

    pdf.save()
    return buffer.getvalue()


def student_ledger_export_response(student, export_format):
    summary = student_finance_summary(student)
    if export_format == "pdf":
        content = _pdf_content(summary)
        content_type = "application/pdf"
    else:
        content = _xlsx_content(summary)
        content_type = XLSX_CONTENT_TYPE
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = (
        f'attachment; filename="{_filename(student, export_format)}"'
    )
    return response
