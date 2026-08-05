from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from string import Formatter
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.cache import cache
from django.core.validators import URLValidator, validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q

from admin_app.models import SystemSetting


CACHE_KEY = "ums.system_settings.v1"
SETTINGS_KEY_PREFIX = "ums."
LEGACY_SETTINGS_KEY_PREFIX = "portal."


OPTIONAL_FEATURES = {
    "admissions": "enable_admissions",
    "public_website": "enable_public_website",
    "venue_booking": "enable_venue_booking",
    "canteen": "enable_canteen",
    "library": "enable_library",
    "library_laptops": "enable_library_laptops",
    "library_rooms": "enable_library_rooms",
    "ict_helpdesk": "enable_ict_helpdesk",
    "hostel": "enable_hostel",
    "elections": "enable_elections",
    "finance": "enable_finance",
    "attendance": "enable_attendance",
    "evaluations": "enable_evaluations",
    "leave": "enable_leave",
    "notifications": "enable_notifications",
    "fines": "enable_fines",
    "quizzes": "enable_quizzes",
}


FEATURE_PATH_SETTINGS = {
    "admissions": ("admissions",),
    "apply": ("admissions",),
    "elections": ("elections",),
    "venue-bookings": ("venue_booking",),
    "venues": ("venue_booking",),
    "canteen": ("canteen",),
    "caterer": ("canteen",),
    "caterers": ("canteen",),
    "library": ("library",),
    "librarian": ("library",),
    "librarians": ("library",),
    "library-laptops": ("library", "library_laptops"),
    "library-rooms": ("library", "library_rooms"),
    "ict-helpdesk": ("ict_helpdesk",),
    "helpdesk": ("ict_helpdesk",),
    "technicians": ("ict_helpdesk",),
    "hostels": ("hostel",),
    "accountant": ("finance",),
    "finance": ("finance",),
    "subscriptions": ("finance",),
    "attendance": ("attendance",),
    "evaluations": ("evaluations",),
    "leave": ("leave",),
    "notifications": ("notifications",),
    "quizzes": ("quizzes",),
    "quiz": ("quizzes",),
    "fines": ("fines",),
}


LOADING_SPINNER_CHOICES = [
    {"value": "audio", "label": "Audio"},
    {"value": "ball-triangle", "label": "Ball Triangle"},
    {"value": "bars", "label": "Bars"},
    {"value": "blocks", "label": "Blocks"},
    {"value": "circles-with-bar", "label": "Circles With Bar"},
    {"value": "circles", "label": "Circles"},
    {"value": "circular-progress", "label": "Circular Progress"},
    {"value": "color-ring", "label": "Color Ring"},
    {"value": "comment", "label": "Comment"},
    {"value": "discuss", "label": "Discuss"},
    {"value": "dna", "label": "DNA"},
    {"value": "falling-lines", "label": "Falling Lines"},
    {"value": "fidget-spinner", "label": "Fidget Spinner"},
    {"value": "grid", "label": "Grid"},
    {"value": "hearts", "label": "Hearts"},
    {"value": "hourglass", "label": "Hourglass"},
    {"value": "infinity-spin", "label": "Infinity Spin"},
    {"value": "line-wave", "label": "Line Wave"},
    {"value": "magnifying-glass", "label": "Magnifying Glass"},
    {"value": "mutating-dots", "label": "Mutating Dots"},
    {"value": "oval", "label": "Oval"},
    {"value": "progress-bar", "label": "Progress Bar"},
    {"value": "puff", "label": "Puff"},
    {"value": "radio", "label": "Radio"},
    {"value": "revolving-dot", "label": "Revolving Dot"},
    {"value": "rings", "label": "Rings"},
    {"value": "rotating-lines", "label": "Rotating Lines"},
    {"value": "rotating-square", "label": "Rotating Square"},
    {"value": "rotating-triangles", "label": "Rotating Triangles"},
    {"value": "tail-spin", "label": "Tail Spin"},
    {"value": "three-circles", "label": "Three Circles"},
    {"value": "three-dots", "label": "Three Dots"},
    {"value": "triangle", "label": "Triangle"},
    {"value": "vortex", "label": "Vortex"},
    {"value": "watch", "label": "Watch"},
]


CORE_ROLE_DEFAULTS = {
    "applicant": {
        "label": "Applicant",
        "short_label": "Applicant",
        "description": "Admissions applicant workspace.",
    },
    "student": {
        "label": "Student",
        "short_label": "Student",
        "description": "Learner workspace for academic and campus services.",
    },
    "teacher": {
        "label": "Teacher",
        "short_label": "Teacher",
        "description": "Teaching workspace for courses, attendance, and assessments.",
    },
    "executive": {
        "label": "Executive",
        "short_label": "Executive",
        "description": "Academic or administrative owner workspace.",
    },
    "librarian": {
        "label": "Librarian",
        "short_label": "Library",
        "description": "Library operations and circulation workspace.",
    },
    "caterer": {
        "label": "Caterer",
        "short_label": "Dining",
        "description": "Dining or canteen checkout workspace.",
    },
    "technician": {
        "label": "Technician",
        "short_label": "Support",
        "description": "Service desk and technical operations workspace.",
    },
    "accountant": {
        "label": "Accountant",
        "short_label": "Finance",
        "description": "Finance, billing, and payment operations workspace.",
    },
    "hr": {
        "label": "Human Resources",
        "short_label": "HR",
        "description": "Human resources and staff operations workspace.",
    },
    "admin": {
        "label": "Admin",
        "short_label": "Admin",
        "description": "Platform administration workspace.",
    },
}


MODULE_LABEL_DEFAULTS = {
    "admissions": "Admissions",
    "public_website": "Public Website",
    "venue_booking": "Venue Booking",
    "canteen": "Dining",
    "library": "Library",
    "library_laptops": "Library Laptops",
    "library_rooms": "Library Rooms",
    "ict_helpdesk": "Service Desk",
    "hostel": "Hostel",
    "elections": "Elections",
    "finance": "Finance",
    "attendance": "Attendance",
    "evaluations": "Evaluations",
    "leave": "Leave",
    "notifications": "Notifications",
    "fines": "Fines",
    "quizzes": "Quizzes",
}


ROLE_MODULE_DEFAULTS = {
    "applicant": ("admissions", "notifications"),
    "student": (
        "venue_booking",
        "canteen",
        "library",
        "library_laptops",
        "library_rooms",
        "ict_helpdesk",
        "hostel",
        "elections",
        "finance",
        "attendance",
        "evaluations",
        "leave",
        "notifications",
        "fines",
        "quizzes",
    ),
    "teacher": (
        "finance",
        "venue_booking",
        "attendance",
        "evaluations",
        "leave",
        "notifications",
        "quizzes",
    ),
    "executive": (
        "venue_booking",
        "elections",
        "finance",
        "attendance",
        "evaluations",
        "notifications",
    ),
    "librarian": ("finance", "library", "library_laptops", "library_rooms", "notifications"),
    "caterer": ("finance", "canteen", "notifications"),
    "technician": ("finance", "ict_helpdesk", "venue_booking", "elections", "notifications"),
    "accountant": ("finance", "canteen", "fines", "notifications"),
    "hr": ("finance", "notifications"),
    "admin": tuple(OPTIONAL_FEATURES),
}


HELPDESK_DEFAULT_CATEGORY_OPTIONS = (
    ("general", "General support"),
    ("hotspot_account", "Account access"),
    ("email_password", "Email or password"),
    ("id_card", "ID card or access card"),
    ("printing_code", "Printing access"),
    ("moodle", "Learning management system"),
    ("email_group", "Email group or mailing list"),
    ("wifi", "Wi-Fi or network"),
    ("facilities", "Facilities support"),
    ("other", "Other support"),
)
HELPDESK_STATUS_ORDER = ("submitted", "addressed", "in_progress", "solved")
HELPDESK_DEFAULT_STATUS_LABELS = (
    ("submitted", "Submitted"),
    ("addressed", "Addressed"),
    ("in_progress", "In progress"),
    ("solved", "Solved"),
)
HELPDESK_ASSIGNMENT_OWNER_TYPES = {
    "technician_id",
    "unit",
    "department",
    "center",
    "school",
}

HOSTEL_DEFAULT_RESIDENCE_TYPE_OPTIONS = (
    ("male", "Male"),
    ("female", "Female"),
    ("mixed", "Mixed residence"),
    ("family", "Family residence"),
    ("staff", "Staff residence"),
)
HOSTEL_DEFAULT_ROOM_CODE_FORMAT = "{hostel}-{floor}-{room}"
HOSTEL_ROOM_CODE_TOKENS = {
    "hostel",
    "hostel_lower",
    "floor",
    "floor_raw",
    "room",
    "room_raw",
}
HOSTEL_BED_ASSIGNMENT_RULE_CHOICES = [
    {"value": "section_letters", "label": "Section letters per bed"},
    {"value": "room_only", "label": "Room only"},
    {"value": "manual", "label": "Manual assignment"},
]

VENUE_BOOKING_DEFAULT_CATEGORY_OPTIONS = (
    ("classroom", "Classroom"),
    ("lecture_hall", "Lecture hall"),
    ("laboratory", "Laboratory"),
    ("auditorium", "Auditorium"),
    ("meeting_room", "Meeting room"),
    ("sports", "Sports facility"),
    ("other", "Other venue"),
)
VENUE_BOOKING_REQUESTER_ROLES = {
    "student": "Student",
    "teacher": "Teacher",
}
VENUE_BOOKING_REVIEWER_ROLE_CHOICES = [
    {"value": "technician", "label": "Technician"},
    {"value": "admin", "label": "Admin"},
]
VENUE_BOOKING_APPROVAL_MODE_CHOICES = [
    {"value": "manual", "label": "Manual review"},
    {"value": "auto_approve", "label": "Auto approve conflict-free requests"},
]
VENUE_BOOKING_REQUIRED_FIELD_CHOICES = {
    "purpose": "Purpose",
    "explanation": "Detailed explanation",
}


def _csv_default(values):
    return ",".join(values)


def field(label, default, field_type="text", **options):
    return {
        "label": label,
        "default": default,
        "type": field_type,
        **options,
    }


def _option_lines(options):
    return "\n".join(f"{value}|{label}" for value, label in options)


def _role_settings_fields():
    fields = {}
    for role, defaults in CORE_ROLE_DEFAULTS.items():
        role_title = defaults["label"]
        fields[f"{role}_label"] = field(
            f"{role_title} role label",
            defaults["label"],
            max_length=80,
        )
        fields[f"{role}_short_label"] = field(
            f"{role_title} short label",
            defaults["short_label"],
            max_length=40,
        )
        fields[f"{role}_description"] = field(
            f"{role_title} description",
            defaults["description"],
            "textarea",
            max_length=240,
        )
        fields[f"{role}_enabled_modules"] = field(
            f"{role_title} enabled modules",
            _csv_default(ROLE_MODULE_DEFAULTS[role]),
            "textarea",
            max_length=500,
            high_impact=True,
            help_text=(
                "Comma-separated module keys. Valid keys: "
                f"{', '.join(OPTIONAL_FEATURES)}."
            ),
        )

    for module, label in MODULE_LABEL_DEFAULTS.items():
        fields[f"module_{module}_label"] = field(
            f"{label} navigation label",
            label,
            max_length=80,
        )

    fields.update(
        {
            "librarian_default_center_code": field(
                "Default librarian center code",
                "",
                required=False,
                max_length=40,
                high_impact=True,
                help_text="Optional fallback center used when a librarian account does not select an owner.",
            ),
            "librarian_default_unit_code": field(
                "Default librarian unit code",
                "",
                required=False,
                max_length=40,
                high_impact=True,
                help_text="Optional fallback library unit used when a librarian account does not select an owner.",
            ),
            "caterer_default_center_code": field(
                "Default dining center code",
                "",
                required=False,
                max_length=40,
                high_impact=True,
                help_text="Optional fallback center used when a caterer account does not select an owner.",
            ),
            "caterer_default_unit_code": field(
                "Default dining unit code",
                "",
                required=False,
                max_length=40,
                high_impact=True,
                help_text="Optional fallback dining/canteen unit used when a caterer account does not select an owner.",
            ),
            "technician_default_department_code": field(
                "Default service department code",
                "",
                required=False,
                max_length=40,
                high_impact=True,
                help_text="Optional fallback department used when a technician account does not select an owner.",
            ),
            "technician_default_unit_code": field(
                "Default service unit code",
                "",
                required=False,
                max_length=40,
                high_impact=True,
                help_text="Optional fallback service desk/IT unit used when a technician account does not select an owner.",
            ),
        }
    )
    return fields


SETTINGS_SECTIONS = {
    "general": {
        "title": "General Platform Settings",
        "description": "Portal support contacts and system-wide operational messaging.",
        "fields": {
            "ums_name": field("Portal name", "University Portal", max_length=120),
            "support_email": field("Support email", "support@example.edu", "email"),
            "support_phone": field("Support phone", "+00 000 000 0000", "tel", max_length=40),
            "maintenance_banner": field(
                "Portal banner message",
                "",
                "textarea",
                required=False,
                max_length=500,
                help_text="Shown as a portal-wide operational announcement when supported by the client.",
            ),
        },
    },
    "university": {
        "title": "Institution Profile",
        "description": "Public institution identity, contact details, and brand images shown across the site.",
        "fields": {
            "university_name": field("University name", "Your University", max_length=180),
            "short_name": field("Short name", "UNI", max_length=40),
            "legal_name": field("Legal name", "Your University", max_length=220),
            "tagline": field("Tagline", "Configurable university portal", max_length=160),
            "description": field(
                "Public description",
                "A configurable institution profile powered by the university portal.",
                "textarea",
                max_length=800,
            ),
            "address": field("Address", "University address", "textarea", max_length=500),
            "phone": field("Main phone", "+00 000 000 0000", "tel", max_length=40),
            "email": field("Main email", "info@example.edu", "email"),
            "admissions_email": field("Admissions email", "admissions@example.edu", "email"),
            "website_url": field("Website URL", "https://example.edu", "url", required=False, max_length=500),
            "logo_url": field("Logo image", "/images/ums/ums-logo.svg", "image", required=False, max_length=500),
            "public_hero_image_url": field(
                "Default public hero image",
                "",
                "image",
                required=False,
                max_length=500,
            ),
            "social_image_url": field(
                "Default social image",
                "",
                "image",
                required=False,
                max_length=500,
            ),
            "login_image_url": field(
                "Login image",
                "",
                "image",
                required=False,
                max_length=500,
            ),
            "favicon_url": field(
                "Favicon",
                "",
                "image",
                required=False,
                max_length=500,
            ),
        },
    },
    "localization": {
        "title": "Localization",
        "description": "Timezone, locale, currency, and date/time formatting defaults.",
        "fields": {
            "timezone": field(
                "Default timezone",
                "UTC",
                help_text="Use an IANA timezone such as UTC, America/New_York, Europe/London, or Asia/Singapore.",
                max_length=80,
                high_impact=True,
            ),
            "locale": field(
                "Locale",
                "en-US",
                max_length=20,
                help_text="Use a BCP 47 locale such as en-US, en-GB, ms-MY, or ar-SA.",
            ),
            "currency_code": field(
                "Currency code",
                "USD",
                max_length=3,
                help_text="Three-letter ISO 4217 currency code.",
                high_impact=True,
            ),
            "currency_symbol": field("Currency symbol", "$", max_length=8),
            "number_format": field(
                "Number format",
                "1,234.56",
                "select",
                choices=[
                    {"value": "1,234.56", "label": "1,234.56"},
                    {"value": "1.234,56", "label": "1.234,56"},
                    {"value": "1 234,56", "label": "1 234,56"},
                    {"value": "1234.56", "label": "1234.56"},
                ],
            ),
            "date_format": field(
                "Date format",
                "YYYY-MM-DD",
                "select",
                choices=[
                    {"value": "YYYY-MM-DD", "label": "YYYY-MM-DD"},
                    {"value": "MM/DD/YYYY", "label": "MM/DD/YYYY"},
                    {"value": "DD/MM/YYYY", "label": "DD/MM/YYYY"},
                    {"value": "DD MMM YYYY", "label": "DD MMM YYYY"},
                ],
            ),
            "time_format": field(
                "Time format",
                "HH:mm",
                "select",
                choices=[
                    {"value": "HH:mm", "label": "24-hour (HH:mm)"},
                    {"value": "h:mm a", "label": "12-hour (h:mm AM/PM)"},
                ],
            ),
        },
    },
    "terminology": {
        "title": "Terminology",
        "description": "Institution-specific labels for academic structure and user identifiers.",
        "fields": {
            "school_label": field("School label", "School", max_length=60),
            "center_label": field("Center label", "Center", max_length=60),
            "department_label": field("Department label", "Department", max_length=60),
            "unit_label": field("Unit label", "Unit", max_length=60),
            "program_label": field("Program label", "Program", max_length=60),
            "course_label": field("Course label", "Course", max_length=60),
            "semester_label": field("Semester label", "Semester", max_length=60),
            "academic_year_label": field("Academic year label", "Academic Year", max_length=60),
            "student_id_label": field("Student ID label", "Student ID", max_length=60),
            "staff_id_label": field("Staff ID label", "Staff ID", max_length=60),
            "applicant_label": field("Applicant label", "Applicant", max_length=60),
        },
    },
    "academic": {
        "title": "Academic Defaults",
        "description": "Defaults used when academic workflows create new records or send warnings.",
        "fields": {
            "default_academic_session": field("Default academic session", "2025/2026", max_length=30),
            "default_semester_type": field(
                "Default semester type",
                "long",
                "select",
                choices=[
                    {"value": "long", "label": "Long semester"},
                    {"value": "short", "label": "Short semester"},
                ],
            ),
            "default_academic_calendar_type": field(
                "Default academic calendar type",
                "semester",
                "select",
                choices=[
                    {"value": "semester", "label": "Semester"},
                    {"value": "trimester", "label": "Trimester"},
                    {"value": "quarter", "label": "Quarter"},
                    {"value": "term", "label": "Term"},
                    {"value": "year_round", "label": "Year-round"},
                ],
                high_impact=True,
            ),
            "registration_min_credit_hours": field(
                "Minimum registration credits",
                9,
                "number",
                min=0,
                max=40,
                high_impact=True,
            ),
            "registration_max_credit_hours": field(
                "Maximum registration credits",
                21,
                "number",
                min=1,
                max=40,
                high_impact=True,
            ),
            "allow_late_registration": field(
                "Allow late registration by default",
                False,
                "boolean",
                high_impact=True,
            ),
            "registration_credit_limit_overrides": field(
                "Registration credit limit overrides",
                "",
                "textarea",
                required=False,
                max_length=1000,
                high_impact=True,
                help_text=(
                    "One rule per line: scope,min,max. Scope can be a program code, "
                    "calendar group, school:CODE, or center:CODE."
                ),
            ),
            "registration_enforce_prerequisites": field(
                "Enforce prerequisites during registration",
                True,
                "boolean",
                high_impact=True,
            ),
            "registration_allow_passed_course_retake": field(
                "Allow retake of passed courses",
                False,
                "boolean",
                high_impact=True,
            ),
            "attendance_threshold_percent": field(
                "Attendance warning threshold (%)",
                80,
                "number",
                min=1,
                max=100,
                high_impact=True,
            ),
            "attendance_warning_minimum_classes": field(
                "Minimum classes before warning",
                5,
                "number",
                min=1,
                max=100,
            ),
            "attendance_code_expiry_minutes": field(
                "Attendance code expiry (minutes)",
                1,
                "number",
                min=1,
                max=180,
            ),
            "evaluation_activity_label": field(
                "Evaluation activity label",
                "Course Evaluation",
                max_length=80,
            ),
            "evaluation_template_name": field(
                "Default evaluation template name",
                "Course Evaluation Standard Template",
                max_length=120,
            ),
            "evaluation_template_description": field(
                "Default evaluation template description",
                "Standard course-content and teaching evaluation template.",
                "textarea",
                max_length=300,
            ),
            "evaluation_required_by_default": field(
                "Make new evaluations required by default",
                True,
                "boolean",
                high_impact=True,
            ),
            "evaluation_registration_gate_enabled": field(
                "Block registration for incomplete required evaluations",
                True,
                "boolean",
                high_impact=True,
            ),
            "grade_point_label": field("Grade point label", "Grade Point", max_length=40),
            "gpa_label": field("GPA label", "GPA", max_length=40),
            "cgpa_label": field("CGPA label", "CGPA", max_length=40),
            "grade_scale_heading": field("Grade scale heading", "Grade Scale", max_length=80),
            "grade_scale_description": field(
                "Grade scale description",
                "Institutional grading scale used for grade point calculation.",
                "textarea",
                max_length=240,
            ),
            "academic_standing_good_label": field(
                "Good standing label",
                "Good Standing",
                max_length=80,
            ),
            "academic_standing_probation_label": field(
                "Academic probation label",
                "Academic Probation",
                max_length=80,
            ),
            "academic_standing_good_min_points": field(
                "Good standing minimum points",
                2,
                "number",
                min=0,
                max=4,
            ),
            "assignment_late_submission_default": field(
                "Allow assignment late submissions by default",
                False,
                "boolean",
                high_impact=True,
            ),
        },
    },
    "workflow": {
        "title": "Workflow Defaults",
        "description": "Default timing, approval, export, and upload rules for portal workflows.",
        "fields": {
            "venue_booking_min_notice_days": field(
                "Venue booking minimum notice (days)",
                1,
                "number",
                min=0,
                max=365,
            ),
            "venue_booking_cancellation_hours": field(
                "Venue booking cancellation deadline (hours)",
                24,
                "number",
                min=0,
                max=720,
            ),
            "leave_request_min_notice_days": field(
                "Leave request minimum notice (days)",
                0,
                "number",
                min=0,
                max=365,
            ),
            "leave_approval_roles": field(
                "Leave approval roles",
                "teacher,dean",
                "textarea",
                max_length=120,
                help_text="Comma-separated values from: teacher, dean.",
                high_impact=True,
            ),
            "leave_approval_order": field(
                "Leave approval order",
                "parallel",
                "select",
                choices=[
                    {"value": "parallel", "label": "Parallel approvals"},
                    {"value": "configured_sequence", "label": "Configured sequence"},
                ],
                high_impact=True,
            ),
            "leave_dean_approver_identifiers": field(
                "Leave dean approver identifiers",
                "",
                "textarea",
                required=False,
                max_length=500,
                help_text="Comma-separated teacher usernames, email addresses, or staff IDs.",
                high_impact=True,
            ),
            "default_approval_mode": field(
                "Default approval mode",
                "automatic_when_unassigned",
                "select",
                choices=[
                    {"value": "manual", "label": "Manual approval"},
                    {"value": "automatic_when_unassigned", "label": "Automatic when no approver exists"},
                ],
                high_impact=True,
            ),
            "report_export_expiry_days": field(
                "Report export expiry (days)",
                30,
                "number",
                min=1,
                max=365,
            ),
            "applicant_max_upload_mb": field(
                "Applicant document maximum size (MB)",
                5,
                "number",
                min=1,
                max=50,
            ),
            "applicant_allowed_file_extensions": field(
                "Applicant allowed file extensions",
                "pdf,jpg,jpeg,png,webp,heic,heif",
                help_text="Comma-separated extensions without dots.",
                max_length=200,
            ),
            "default_upload_limit_mb": field(
                "Default upload limit (MB)",
                10,
                "number",
                min=1,
                max=100,
            ),
            "default_allowed_file_extensions": field(
                "Default allowed file extensions",
                "pdf,jpg,jpeg,png,webp",
                help_text="Comma-separated extensions without dots.",
                max_length=200,
            ),
            "default_application_number_prefix": field(
                "Default application number prefix",
                "APP",
                max_length=16,
                help_text="Used for newly generated application numbers.",
                high_impact=True,
            ),
            "default_payment_gateway_provider": field(
                "Default payment gateway provider",
                "manual",
                "select",
                choices=[
                    {"value": "manual", "label": "Manual / offline"},
                    {"value": "toyyibpay", "label": "External bill API"},
                    {"value": "stripe", "label": "Stripe"},
                    {"value": "other", "label": "Other"},
                ],
                high_impact=True,
            ),
            "payment_reference_prefix": field(
                "Payment reference prefix",
                "PORTAL",
                max_length=20,
                help_text="Used for newly generated finance payment references.",
                high_impact=True,
            ),
        },
    },
    "notifications": {
        "title": "Notifications",
        "description": "Control which workflow events create notifications and how portal messages are identified.",
        "fields": {
            "email_notifications_enabled": field(
                "Enable email notifications",
                True,
                "boolean",
                high_impact=True,
            ),
            "notify_assignments": field("Assignment notifications", True, "boolean"),
            "notify_sec_set_reminders": field("SEC-SET reminder notifications", True, "boolean"),
            "notify_library_due_reminders": field("Library due reminders", True, "boolean"),
            "notify_attendance_warnings": field("Attendance warning notifications", True, "boolean"),
            "notify_approvals": field("Approval workflow notifications", True, "boolean"),
            "notify_elections": field("Election notifications", True, "boolean"),
            "notify_applications": field("Application notifications", True, "boolean"),
            "sender_display_name": field("Sender display name", "University Portal", max_length=120),
        },
    },
    "dashboard": {
        "title": "Feature Availability",
        "description": "Enable or disable optional portal features.",
        "fields": {
            "enable_admissions": field("Enable admissions", True, "boolean", high_impact=True),
            "enable_public_website": field("Enable public website", True, "boolean", high_impact=True),
            "enable_venue_booking": field("Enable venue booking", True, "boolean", high_impact=True),
            "enable_canteen": field("Enable canteen", True, "boolean", high_impact=True),
            "enable_library": field("Enable library", True, "boolean", high_impact=True),
            "enable_library_laptops": field("Enable library laptop borrowing", True, "boolean", high_impact=True),
            "enable_library_rooms": field("Enable library discussion room booking", True, "boolean", high_impact=True),
            "enable_ict_helpdesk": field("Enable service desk", True, "boolean", high_impact=True),
            "enable_hostel": field("Enable hostel management", True, "boolean", high_impact=True),
            "enable_elections": field("Enable elections", True, "boolean", high_impact=True),
            "enable_finance": field("Enable finance", True, "boolean", high_impact=True),
            "enable_attendance": field("Enable attendance", True, "boolean", high_impact=True),
            "enable_evaluations": field("Enable evaluations", True, "boolean", high_impact=True),
            "enable_leave": field("Enable leave", True, "boolean", high_impact=True),
            "enable_notifications": field("Enable notifications", True, "boolean", high_impact=True),
            "enable_fines": field("Enable fines and charges", True, "boolean", high_impact=True),
            "enable_quizzes": field("Enable quizzes", True, "boolean", high_impact=True),
        },
    },
    "helpdesk": {
        "title": "Service Desk Settings",
        "description": "Configure student service desk labels, categories, references, and category routing.",
        "fields": {
            "helpdesk_display_label": field(
                "Display label",
                "Service Desk",
                max_length=80,
                help_text="Visible title used on student and technician ticket pages.",
            ),
            "helpdesk_reference_prefix": field(
                "Ticket reference prefix",
                "SD",
                max_length=20,
                high_impact=True,
                help_text="Used for generated ticket references. Letters, numbers, hyphens, and underscores are allowed.",
            ),
            "helpdesk_category_options": field(
                "Ticket categories",
                _option_lines(HELPDESK_DEFAULT_CATEGORY_OPTIONS),
                "textarea",
                max_length=4000,
                high_impact=True,
                help_text="One category per line as code|Label. Codes may contain letters, numbers, hyphens, or underscores.",
            ),
            "helpdesk_status_labels": field(
                "Ticket status labels",
                _option_lines(HELPDESK_DEFAULT_STATUS_LABELS),
                "textarea",
                max_length=1000,
                high_impact=True,
                help_text="One status label per line as status|Label. Status values stay submitted, addressed, in_progress, and solved.",
            ),
            "helpdesk_assignment_rules": field(
                "Category assignment rules",
                "",
                "textarea",
                required=False,
                max_length=4000,
                high_impact=True,
                help_text=(
                    "Optional. One rule per line as category|owner_type|owner_code. "
                    "Owner types: technician_id, unit, department, center, school."
                ),
            ),
        },
    },
    "venue_booking_policy": {
        "title": "Venue Booking Policy",
        "description": "Configure venue categories, requester roles, approval owner, blackout dates, duration limits, and required booking fields.",
        "fields": {
            "venue_category_options": field(
                "Venue categories",
                _option_lines(VENUE_BOOKING_DEFAULT_CATEGORY_OPTIONS),
                "textarea",
                max_length=1600,
                high_impact=True,
                help_text="One category per line as code|Label. Codes are stored on venues and must be 40 characters or fewer.",
            ),
            "requester_roles": field(
                "Requester roles",
                _csv_default(VENUE_BOOKING_REQUESTER_ROLES),
                "textarea",
                max_length=120,
                high_impact=True,
                help_text="Comma-separated requester roles. Supported values: student, teacher.",
            ),
            "approval_mode": field(
                "Approval mode",
                "manual",
                "select",
                choices=VENUE_BOOKING_APPROVAL_MODE_CHOICES,
                high_impact=True,
            ),
            "reviewer_role": field(
                "Manual reviewer role",
                "technician",
                "select",
                choices=VENUE_BOOKING_REVIEWER_ROLE_CHOICES,
                high_impact=True,
            ),
            "blackout_dates": field(
                "Blackout dates",
                "",
                "textarea",
                required=False,
                max_length=3000,
                high_impact=True,
                help_text="One date or date range per line, using YYYY-MM-DD or YYYY-MM-DD..YYYY-MM-DD.",
            ),
            "min_duration_minutes": field(
                "Minimum booking duration (minutes)",
                30,
                "number",
                min=1,
                max=1440,
                high_impact=True,
            ),
            "max_duration_hours": field(
                "Maximum booking duration (hours)",
                8,
                "number",
                min=1,
                max=24,
                high_impact=True,
            ),
            "required_fields_event": field(
                "Required event fields",
                "purpose,explanation",
                "textarea",
                required=False,
                max_length=120,
                high_impact=True,
                help_text="Comma-separated fields required for event bookings. Supported values: purpose, explanation.",
            ),
            "required_fields_personal": field(
                "Required personal-use fields",
                "purpose,explanation",
                "textarea",
                required=False,
                max_length=120,
                high_impact=True,
                help_text="Comma-separated fields required for personal bookings. Supported values: purpose, explanation.",
            ),
        },
    },
    "hostel_policy": {
        "title": "Hostel Policy",
        "description": "Configure residence type labels, room capacities, room code generation, bed assignment, and eligibility guidance.",
        "fields": {
            "residence_type_options": field(
                "Residence type options",
                _option_lines(HOSTEL_DEFAULT_RESIDENCE_TYPE_OPTIONS),
                "textarea",
                max_length=1200,
                high_impact=True,
                help_text="One residence type per line as code|Label. Codes are stored on hostels and must be 10 characters or fewer.",
            ),
            "default_room_capacity": field(
                "Default room capacity",
                4,
                "number",
                min=1,
                max=99,
                help_text="Used when a new room is created without an explicit capacity.",
            ),
            "max_room_capacity": field(
                "Maximum room capacity",
                26,
                "number",
                min=1,
                max=99,
                high_impact=True,
                help_text="Upper limit accepted by hostel room forms and APIs.",
            ),
            "room_code_format": field(
                "Room code format",
                HOSTEL_DEFAULT_ROOM_CODE_FORMAT,
                max_length=120,
                high_impact=True,
                help_text="Available tokens: {hostel}, {hostel_lower}, {floor}, {floor_raw}, {room}, {room_raw}.",
            ),
            "bed_assignment_rule": field(
                "Bed assignment rule",
                "section_letters",
                "select",
                choices=HOSTEL_BED_ASSIGNMENT_RULE_CHOICES,
                high_impact=True,
            ),
            "eligibility_rules": field(
                "Hostel eligibility rules",
                "",
                "textarea",
                required=False,
                max_length=2000,
                help_text="Optional admin note describing who is eligible for hostel assignment.",
            ),
        },
    },
    "roles": {
        "title": "Role, Permission, Navigation, and Module Ownership",
        "description": "Configure role display text, role-module visibility, navigation labels, and fallback ownership for special staff roles.",
        "fields": _role_settings_fields(),
    },
    "security": {
        "title": "Security and Access",
        "description": "High-impact access policies. Administrators retain access to settings and audit logs.",
        "fields": {
            "applicant_registration_enabled": field(
                "Enable applicant self-registration",
                True,
                "boolean",
                high_impact=True,
            ),
            "maintenance_mode": field(
                "Maintenance mode",
                False,
                "boolean",
                high_impact=True,
            ),
            "read_only_mode": field(
                "Read-only mode",
                False,
                "boolean",
                high_impact=True,
            ),
            "session_inactivity_minutes": field(
                "Session inactivity policy (minutes)",
                30,
                "number",
                min=5,
                max=1440,
                high_impact=True,
            ),
            "password_min_length": field(
                "Minimum password length",
                8,
                "number",
                min=8,
                max=20,
                high_impact=True,
            ),
            "password_max_length": field(
                "Maximum password length",
                20,
                "number",
                min=8,
                max=20,
                high_impact=True,
            ),
            "password_require_uppercase": field(
                "Require uppercase password character",
                False,
                "boolean",
                high_impact=True,
            ),
            "password_require_number": field(
                "Require numeric password character",
                True,
                "boolean",
                high_impact=True,
            ),
        },
    },
    "canteen_policy": {
        "title": "Dining/Canteen Policy",
        "description": "Control dining allowance amount, reset boundary, eligibility, and balance synchronization.",
        "fields": {
            "monthly_allowance_amount": field(
                "Monthly allowance amount",
                "50.00",
                max_length=20,
                high_impact=True,
                help_text="Stored in the configured finance currency.",
            ),
            "allowance_reset_timezone": field(
                "Allowance reset timezone",
                "",
                required=False,
                max_length=80,
                high_impact=True,
                help_text="Use an IANA timezone, or leave blank to use the institution default timezone.",
            ),
            "allowance_reset_day": field(
                "Allowance reset day",
                1,
                "number",
                min=1,
                max=28,
                high_impact=True,
                help_text="Day of month when a new allowance month becomes active.",
            ),
            "allowance_reset_hour": field(
                "Allowance reset hour",
                8,
                "number",
                min=0,
                max=23,
                high_impact=True,
                help_text="Local hour when the configured reset day switches to the new month.",
            ),
            "eligible_enrollment_statuses": field(
                "Eligible enrollment statuses",
                "",
                "textarea",
                required=False,
                max_length=300,
                high_impact=True,
                help_text="Comma-separated statuses. Leave blank to allow any active status not matched by the ineligible markers.",
            ),
            "ineligible_enrollment_status_markers": field(
                "Ineligible status markers",
                "terminated,graduat,dropout,drop out,withdraw,internship,intern",
                "textarea",
                required=False,
                max_length=300,
                high_impact=True,
                help_text="Comma-separated text fragments that make a student ineligible.",
            ),
            "require_scholarship": field(
                "Require scholarship",
                False,
                "boolean",
                high_impact=True,
                help_text="Only students with scholarship data marked active/approved are eligible.",
            ),
            "eligible_program_codes": field(
                "Eligible program codes",
                "",
                "textarea",
                required=False,
                max_length=500,
                high_impact=True,
                help_text="Comma-separated program codes. Leave blank to allow all programs.",
            ),
            "eligible_cohort_codes": field(
                "Eligible cohort codes",
                "",
                "textarea",
                required=False,
                max_length=500,
                high_impact=True,
                help_text="Comma-separated cohort codes. Leave blank to allow all cohorts.",
            ),
            "sync_balance_to_student_profile": field(
                "Sync balance to student profile",
                True,
                "boolean",
                high_impact=True,
                help_text="When enabled, the current dining balance is mirrored to the student profile balance field.",
            ),
        },
    },
    "librarian_library": {
        "title": "Library Service Settings",
        "description": "Control which library services are available to students. Managed by librarians.",
        "fields": {
            "books_enabled": field("Enable book borrowing", True, "boolean"),
            "laptops_enabled": field("Enable laptop borrowing", True, "boolean"),
            "rooms_enabled": field("Enable discussion room booking", True, "boolean"),
            "other_assets_enabled": field("Enable other library assets", False, "boolean"),
            "book_requests_enabled": field("Allow student book requests", True, "boolean"),
            "laptop_requests_enabled": field("Allow student laptop requests", True, "boolean"),
            "room_reservations_enabled": field("Allow student room reservations", True, "boolean"),
            "other_asset_requests_enabled": field("Allow student other-asset requests", False, "boolean"),
            "book_max_borrow_at_a_time": field("Book borrow limit", 3, "number", min=1, max=99),
            "book_max_keep_at_a_time": field("Book holding limit", 5, "number", min=1, max=99),
            "laptop_max_borrow_at_a_time": field("Laptop borrow limit", 1, "number", min=1, max=99),
            "laptop_max_keep_at_a_time": field("Laptop holding limit", 1, "number", min=1, max=99),
            "room_max_borrow_at_a_time": field("Room reservation limit", 1, "number", min=1, max=99),
            "room_max_keep_at_a_time": field("Room allocation limit", 1, "number", min=1, max=99),
            "other_asset_max_borrow_at_a_time": field("Other asset borrow limit", 1, "number", min=1, max=99),
            "other_asset_max_keep_at_a_time": field("Other asset holding limit", 1, "number", min=1, max=99),
            "book_loan_period_days": field("Book loan period days", 14, "number", min=1, max=365),
            "laptop_loan_period_days": field("Laptop loan period days", 7, "number", min=1, max=365),
            "room_loan_period_hours": field("Room allocation period hours", 2, "number", min=1, max=24),
            "other_asset_loan_period_days": field("Other asset loan period days", 7, "number", min=1, max=365),
            "book_max_renewals": field("Book maximum renewals", 2, "number", min=0, max=12),
            "laptop_max_renewals": field("Laptop maximum renewals", 0, "number", min=0, max=12),
            "room_max_renewals": field("Room maximum renewals", 0, "number", min=0, max=12),
            "other_asset_max_renewals": field("Other asset maximum renewals", 0, "number", min=0, max=12),
            "book_renewal_period_days": field("Book renewal period days", 14, "number", min=1, max=365),
            "laptop_renewal_period_days": field("Laptop renewal period days", 7, "number", min=1, max=365),
            "room_renewal_period_hours": field("Room renewal period hours", 1, "number", min=1, max=24),
            "other_asset_renewal_period_days": field("Other asset renewal period days", 7, "number", min=1, max=365),
            "book_daily_fine_amount": field("Book daily overdue fine", "1.00", "text", max_length=20),
            "laptop_daily_fine_amount": field("Laptop daily overdue fine", "5.00", "text", max_length=20),
            "room_daily_fine_amount": field("Room daily overdue fine", "0.00", "text", max_length=20),
            "other_asset_daily_fine_amount": field("Other asset daily overdue fine", "1.00", "text", max_length=20),
        },
    },
}


UI_CUSTOMIZATION_DEFINITION = {
    "title": "Portal UI Customization",
    "description": "Customize UI appearance, colors, fonts, and backgrounds across the site.",
    "fields": {
        "brand_name": field("Dashboard brand name", "University Portal", max_length=140),
        "sidebar_label": field("Sidebar brand label", "University Portal", max_length=140),
        "logo_url": field("Dashboard logo image", "/images/ums/ums-logo.svg", "image", required=False, max_length=500),
        "logo_alt_text": field("Dashboard logo alt text", "University logo", max_length=140),
        "default_avatar_url": field("Default avatar image", "/images/avatar.png", "image", required=False, max_length=500),
        "loading_spinner": field(
            "Loading screen spinner",
            "dna",
            "select",
            choices=LOADING_SPINNER_CHOICES,
            help_text="Default full-screen loading animation from react-loader-spinner.",
        ),
        "loading_spinner_size": field(
            "Loading spinner size (px)",
            80,
            "number",
            min=32,
            max=160,
            help_text="Controls the width and height of the default loading animation.",
        ),
        "card_density": field(
            "Dashboard card density",
            "comfortable",
            "select",
            choices=[
                {"value": "comfortable", "label": "Comfortable"},
                {"value": "compact", "label": "Compact"},
            ],
        ),
        "show_scope_badge": field("Show dashboard scope badge", True, "boolean"),
        "show_link_descriptions": field("Show dashboard link descriptions", True, "boolean"),
        "primary_text_color": field("Primary text color", "#09090b", "color"),
        "secondary_text_color": field("Secondary text color", "#71717a", "color"),
        "accent_color": field("Accent color", "#0f766e", "color"),
        "background_color": field("Background color", "#ffffff", "color"),
        "font_family": field("Font family", "Inter", "select", choices=[
            {"value": "Inter", "label": "Inter"},
            {"value": "Roboto", "label": "Roboto"},
            {"value": "Outfit", "label": "Outfit"},
            {"value": "Arial", "label": "Arial"},
            {"value": "Helvetica", "label": "Helvetica"}
        ]),
        "font_size_base": field("Base font size (px)", "16", "select", choices=[
            {"value": "12", "label": "12px"},
            {"value": "14", "label": "14px"},
            {"value": "16", "label": "16px (Default)"},
            {"value": "18", "label": "18px"},
            {"value": "20", "label": "20px"},
        ]),
        "dashboard_background_image_url": field("Dashboard background image", "", "image", required=False, max_length=500),
        "button_color": field("Button color", "#18181b", "color"),
        "button_text_color": field("Button text color", "#fafafa", "color"),
        "secondary_button_color": field("Secondary button color", "#f4f4f5", "color"),
        "secondary_button_text_color": field("Secondary button text color", "#18181b", "color"),
        "button_border_radius": field("Button border radius", "0.5rem", "select", choices=[
            {"value": "0", "label": "None (0px)"},
            {"value": "0.25rem", "label": "Small (4px)"},
            {"value": "0.5rem", "label": "Medium (8px)"},
            {"value": "0.625rem", "label": "Large (10px)"},
        ]),
        "icon_color": field("Icon color", "#09090b", "color"),
        "icon_size": field("Icon size", "16px", "select", choices=[
            {"value": "14px", "label": "14px"},
            {"value": "16px", "label": "16px (Default)"},
            {"value": "18px", "label": "18px"},
            {"value": "20px", "label": "20px"},
            {"value": "24px", "label": "24px"},
        ]),
        "dark_primary_text_color": field("Dark mode — Primary text color", "#fafafa", "color"),
        "dark_secondary_text_color": field("Dark mode — Secondary text color", "#a1a1aa", "color"),
        "dark_background_color": field("Dark mode — Background color", "#09090b", "color"),
        "dark_button_color": field("Dark mode — Button color", "#fafafa", "color"),
        "dark_button_text_color": field("Dark mode — Button text color", "#18181b", "color"),
        "dark_secondary_button_color": field("Dark mode — Secondary button color", "#27272a", "color"),
        "dark_secondary_button_text_color": field("Dark mode — Secondary button text color", "#fafafa", "color"),
        "dark_accent_color": field("Dark mode — Accent color", "#fafafa", "color"),
        "dark_icon_color": field("Dark mode — Icon color", "#fafafa", "color"),
        "sidebar_font_size": field("Sidebar font size", "14px", "select", choices=[
            {"value": "12px", "label": "12px"},
            {"value": "13px", "label": "13px"},
            {"value": "14px", "label": "14px (Default)"},
            {"value": "16px", "label": "16px"},
        ]),
        "sidebar_font_weight": field("Sidebar font weight", "medium", "select", choices=[
            {"value": "normal", "label": "Normal (400)"},
            {"value": "medium", "label": "Medium (500)"},
            {"value": "semibold", "label": "Semibold (600)"},
        ]),
        "sidebar_icon_size": field("Sidebar icon size", "16px", "select", choices=[
            {"value": "14px", "label": "14px"},
            {"value": "16px", "label": "16px (Default)"},
            {"value": "18px", "label": "18px"},
            {"value": "20px", "label": "20px"},
        ]),
        "sidebar_width": field(
            "Sidebar width", "16rem", "select", choices=[
                {"value": "14rem", "label": "Narrow (14rem)"},
                {"value": "16rem", "label": "Default (16rem)"},
                {"value": "18rem", "label": "Wide (18rem)"},
            ],
        ),
        "sidebar_collapsed_by_default": field(
            "Start with sidebar collapsed", False, "boolean",
        ),
        "sticky_header": field(
            "Sticky header on scroll", True, "boolean",
        ),
        "show_breadcrumbs": field(
            "Show breadcrumb navigation", True, "boolean",
        ),
        "show_footer": field(
            "Show page footer", True, "boolean",
        ),
        "card_border_radius": field(
            "Card border radius", "0.5rem", "select", choices=[
                {"value": "0", "label": "None (0px)"},
                {"value": "0.375rem", "label": "Small (6px)"},
                {"value": "0.5rem", "label": "Medium (8px)"},
                {"value": "0.75rem", "label": "Large (12px)"},
            ],
        ),
        "card_shadow": field(
            "Card shadow", "default", "select", choices=[
                {"value": "none", "label": "None"},
                {"value": "light", "label": "Light"},
                {"value": "default", "label": "Default"},
                {"value": "strong", "label": "Strong"},
            ],
        ),
        "card_background_color": field("Card background color", "#ffffff", "color"),
        "avatar_shape": field(
            "Avatar shape", "circle", "select", choices=[
                {"value": "circle", "label": "Circle"},
                {"value": "rounded", "label": "Rounded"},
                {"value": "square", "label": "Square"},
            ],
        ),
        "avatar_size": field(
            "Avatar size", "md", "select", choices=[
                {"value": "sm", "label": "Small"},
                {"value": "md", "label": "Medium (Default)"},
                {"value": "lg", "label": "Large"},
            ],
        ),
        "table_stripe_color": field(
            "Table stripe color", "", "color", required=False,
            help_text="Leave empty for no alternating row color.",
        ),
        "modal_overlay_opacity": field(
            "Modal overlay opacity (%)", 50, "number", min=0, max=100,
        ),
    }
}

UI_CUSTOMIZATION_DEFAULTS = {
    key: deepcopy(config["default"])
    for key, config in UI_CUSTOMIZATION_DEFINITION["fields"].items()
}


def setting_key(section):
    return f"{SETTINGS_KEY_PREFIX}{section}"


def section_from_setting_key(key):
    for prefix in (SETTINGS_KEY_PREFIX, LEGACY_SETTINGS_KEY_PREFIX):
        if key.startswith(prefix):
            return key.removeprefix(prefix)
    return key


def defaults_for_section(section):
    return {
        key: deepcopy(config["default"])
        for key, config in SETTINGS_SECTIONS[section]["fields"].items()
    }


def all_settings():
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return deepcopy(cached)

    values = {
        section: defaults_for_section(section)
        for section in SETTINGS_SECTIONS
    }
    records = SystemSetting.objects.filter(
        Q(key__startswith=SETTINGS_KEY_PREFIX)
        | Q(key__startswith=LEGACY_SETTINGS_KEY_PREFIX)
    ).order_by("key")
    for record in records:
        section = section_from_setting_key(record.key)
        if section in values and isinstance(record.value, dict):
            values[section].update(
                {
                    key: value
                    for key, value in record.value.items()
                    if key in SETTINGS_SECTIONS[section]["fields"]
                }
            )
    cache.set(CACHE_KEY, values, timeout=60)
    return deepcopy(values)


def setting_value(section, name):
    return all_settings()[section][name]


def setting_values(section):
    return deepcopy(all_settings()[section])


def localization_settings():
    return setting_values("localization")


def terminology_settings():
    values = setting_values("terminology")
    return {
        **values,
        "centre_label": values["center_label"],
        "programme_label": values["program_label"],
    }


def institution_identity():
    return setting_values("university")


def portal_name():
    name = str(setting_value("general", "ums_name") or "").strip()
    return name or "University Portal"


def institution_name():
    values = institution_identity()
    name = str(
        values.get("university_name")
        or values.get("legal_name")
        or values.get("short_name")
        or ""
    ).strip()
    return name or "Your University"


def institution_short_name():
    values = institution_identity()
    short_name = str(values.get("short_name") or "").strip()
    return short_name or institution_name()


def notification_sender_name():
    name = str(setting_value("notifications", "sender_display_name") or "").strip()
    return name or portal_name()


def institution_timezone():
    timezone_name = str(setting_value("localization", "timezone") or "UTC").strip() or "UTC"
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def default_currency_code():
    code = str(setting_value("localization", "currency_code") or "USD").strip().upper()
    return code if len(code) == 3 and code.isalpha() else "USD"


def currency_symbol():
    return str(setting_value("localization", "currency_symbol") or "").strip()


def format_currency_amount(value, *, currency_code=None, symbol=None):
    default_code = default_currency_code()
    code = str(currency_code or default_code).strip().upper() or default_code
    if symbol is None:
        marker = currency_symbol() if code == default_code else ""
    else:
        marker = str(symbol or "").strip()
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0.00")
    formatted = f"{amount:.2f}"
    if marker:
        separator = "" if len(marker) == 1 else " "
        return f"{marker}{separator}{formatted}"
    return f"{code} {formatted}"


def _reference_prefix(value, fallback):
    normalized = "".join(
        character
        for character in str(value or fallback).strip().upper()
        if character.isalnum() or character in {"-", "_"}
    )
    return (normalized or fallback)[:20]


def _helpdesk_config_lines(value):
    return [
        line.strip()
        for line in str(value or "").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _helpdesk_option_key(value, *, max_length=40):
    normalized = str(value or "").strip().lower().replace(" ", "_")
    normalized = "".join(
        character
        for character in normalized
        if character.isalnum() or character in {"-", "_"}
    )
    return normalized[:max_length]


def _split_helpdesk_pair(line, field_name, line_number):
    for separator in ("|", "="):
        if separator in line:
            left, right = line.split(separator, 1)
            return left.strip(), right.strip()
    raise ValidationError(
        {
            field_name: (
                f"Line {line_number} must use code|Label or code=Label format."
            )
        }
    )


def _parse_helpdesk_options(
    value,
    *,
    field_name,
    allowed_values=None,
    key_max_length=40,
    label_max_length=80,
):
    options = []
    seen = set()
    for line_number, line in enumerate(_helpdesk_config_lines(value), start=1):
        raw_key, label = _split_helpdesk_pair(line, field_name, line_number)
        full_key = _helpdesk_option_key(raw_key, max_length=255)
        if len(full_key) > key_max_length:
            raise ValidationError(
                {
                    field_name: (
                        f"Line {line_number} code must be "
                        f"{key_max_length} characters or fewer."
                    )
                }
            )
        key = _helpdesk_option_key(raw_key, max_length=key_max_length)
        if not key:
            raise ValidationError({field_name: f"Line {line_number} has an empty code."})
        if allowed_values and key not in allowed_values:
            raise ValidationError(
                {field_name: f"Line {line_number} uses unknown status '{key}'."}
            )
        if key in seen:
            raise ValidationError({field_name: f"Duplicate code '{key}'."})
        if not label:
            raise ValidationError({field_name: f"Line {line_number} has an empty label."})
        if len(label) > label_max_length:
            raise ValidationError(
                {
                    field_name: (
                        f"Line {line_number} label must be "
                        f"{label_max_length} characters or fewer."
                    )
                }
            )
        seen.add(key)
        options.append((key, label))
    if not options:
        raise ValidationError({field_name: "Provide at least one option."})
    return options


def _normalize_helpdesk_options(
    value,
    *,
    field_name,
    allowed_values=None,
    key_max_length=40,
    label_max_length=80,
):
    return _option_lines(
        _parse_helpdesk_options(
            value,
            field_name=field_name,
            allowed_values=allowed_values,
            key_max_length=key_max_length,
            label_max_length=label_max_length,
        )
    )


def _normalize_hostel_residence_type_options(value):
    return _normalize_helpdesk_options(
        value,
        field_name="residence_type_options",
        key_max_length=10,
        label_max_length=80,
    )


def _normalize_venue_category_options(value):
    return _normalize_helpdesk_options(
        value,
        field_name="venue_category_options",
        key_max_length=40,
        label_max_length=80,
    )


def _normalize_csv_setting_keys(value, *, field_name, allowed_values, allow_empty=False):
    keys = [
        _helpdesk_option_key(item)
        for item in str(value or "").split(",")
        if str(item or "").strip()
    ]
    keys = list(dict.fromkeys(keys))
    if not keys and not allow_empty:
        raise ValidationError({field_name: "Provide at least one value."})
    unknown = sorted(set(keys) - set(allowed_values))
    if unknown:
        raise ValidationError(
            {field_name: f"Unknown value(s): {', '.join(unknown)}."}
        )
    return ",".join(keys)


def _normalize_venue_requester_roles(value):
    return _normalize_csv_setting_keys(
        value,
        field_name="requester_roles",
        allowed_values=set(VENUE_BOOKING_REQUESTER_ROLES),
    )


def _normalize_venue_required_fields(value, *, field_name):
    return _normalize_csv_setting_keys(
        value,
        field_name=field_name,
        allowed_values=set(VENUE_BOOKING_REQUIRED_FIELD_CHOICES),
        allow_empty=True,
    )


def _parse_venue_blackout_date(value, *, field_name, line_number):
    try:
        return date.fromisoformat(str(value or "").strip())
    except ValueError:
        raise ValidationError(
            {field_name: f"Line {line_number} must use YYYY-MM-DD dates."}
        ) from None


def _parse_venue_blackout_ranges(value, *, field_name="blackout_dates"):
    ranges = []
    for line_number, line in enumerate(_helpdesk_config_lines(value), start=1):
        if ".." in line:
            raw_start, raw_end = line.split("..", 1)
        elif "|" in line:
            raw_start, raw_end = line.split("|", 1)
        else:
            raw_start = raw_end = line
        start = _parse_venue_blackout_date(
            raw_start,
            field_name=field_name,
            line_number=line_number,
        )
        end = _parse_venue_blackout_date(
            raw_end,
            field_name=field_name,
            line_number=line_number,
        )
        if end < start:
            raise ValidationError(
                {field_name: f"Line {line_number} range end must be on or after the start date."}
            )
        ranges.append((start, end))
    return ranges


def _normalize_venue_blackout_dates(value):
    ranges = _parse_venue_blackout_ranges(value)
    return "\n".join(
        start.isoformat() if start == end else f"{start.isoformat()}..{end.isoformat()}"
        for start, end in ranges
    )


def _hostel_room_code_tokens(value):
    tokens = []
    try:
        parsed = list(Formatter().parse(str(value or "")))
    except ValueError:
        raise ValidationError(
            {"room_code_format": "Use valid Python-style tokens such as {hostel}-{floor}-{room}."}
        ) from None
    for _literal, field_name, _format_spec, _conversion in parsed:
        if not field_name:
            continue
        token = field_name.split(".", 1)[0].split("[", 1)[0]
        tokens.append(token)
    return tokens


def _validate_hostel_room_code_format(value):
    tokens = set(_hostel_room_code_tokens(value))
    unknown = sorted(tokens - HOSTEL_ROOM_CODE_TOKENS)
    if unknown:
        raise ValidationError(
            {
                "room_code_format": (
                    "Unknown token(s): "
                    f"{', '.join(unknown)}. Use {', '.join(sorted(HOSTEL_ROOM_CODE_TOKENS))}."
                )
            }
        )
    required_groups = {
        "hostel": {"hostel", "hostel_lower"},
        "floor": {"floor", "floor_raw"},
        "room": {"room", "room_raw"},
    }
    missing = [
        label
        for label, choices in required_groups.items()
        if not tokens.intersection(choices)
    ]
    if missing:
        raise ValidationError(
            {
                "room_code_format": (
                    "Include hostel, floor, and room tokens so generated codes stay unique."
                )
            }
        )


def _validate_hostel_policy_settings(values):
    _parse_helpdesk_options(
        values.get("residence_type_options"),
        field_name="residence_type_options",
        key_max_length=10,
        label_max_length=80,
    )
    if values["default_room_capacity"] > values["max_room_capacity"]:
        raise ValidationError(
            {
                "max_room_capacity": (
                    "Maximum room capacity must be at least the default room capacity."
                )
            }
        )
    _validate_hostel_room_code_format(values.get("room_code_format"))


def _validate_venue_booking_policy_settings(values):
    _parse_helpdesk_options(
        values.get("venue_category_options"),
        field_name="venue_category_options",
        key_max_length=40,
        label_max_length=80,
    )
    _normalize_venue_requester_roles(values.get("requester_roles"))
    _parse_venue_blackout_ranges(values.get("blackout_dates"))
    _normalize_venue_required_fields(
        values.get("required_fields_event"),
        field_name="required_fields_event",
    )
    _normalize_venue_required_fields(
        values.get("required_fields_personal"),
        field_name="required_fields_personal",
    )
    if values["min_duration_minutes"] > values["max_duration_hours"] * 60:
        raise ValidationError(
            {
                "max_duration_hours": (
                    "Maximum booking duration must be at least the minimum booking duration."
                )
            }
        )


def _parse_helpdesk_assignment_rules(value):
    rules = []
    seen = set()
    for line_number, line in enumerate(_helpdesk_config_lines(value), start=1):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3:
            raise ValidationError(
                {
                    "helpdesk_assignment_rules": (
                        f"Line {line_number} must use category|owner_type|owner_code format."
                    )
                }
            )
        category = _helpdesk_option_key(parts[0])
        owner_type = parts[1].lower()
        if owner_type == "technician":
            owner_type = "technician_id"
        owner_code = parts[2].strip()
        if owner_type != "technician_id":
            owner_code = owner_code.upper()
        if not category or not owner_code:
            raise ValidationError(
                {
                    "helpdesk_assignment_rules": (
                        f"Line {line_number} must include a category and owner code."
                    )
                }
            )
        if owner_type not in HELPDESK_ASSIGNMENT_OWNER_TYPES:
            raise ValidationError(
                {
                    "helpdesk_assignment_rules": (
                        f"Line {line_number} has unsupported owner type '{parts[1]}'."
                    )
                }
            )
        if category in seen:
            raise ValidationError(
                {"helpdesk_assignment_rules": f"Duplicate rule for category '{category}'."}
            )
        seen.add(category)
        rules.append(
            {
                "category": category,
                "owner_type": owner_type,
                "owner_code": owner_code,
            }
        )
    return rules


def _normalize_helpdesk_assignment_rules(value):
    return "\n".join(
        f"{rule['category']}|{rule['owner_type']}|{rule['owner_code']}"
        for rule in _parse_helpdesk_assignment_rules(value)
    )


def _helpdesk_default_option_map(options):
    return {value: label for value, label in options}


def _safe_helpdesk_options(
    value,
    *,
    field_name,
    fallback,
    allowed_values=None,
    key_max_length=40,
    label_max_length=80,
):
    try:
        return _parse_helpdesk_options(
            value,
            field_name=field_name,
            allowed_values=allowed_values,
            key_max_length=key_max_length,
            label_max_length=label_max_length,
        )
    except ValidationError:
        return list(fallback)


def _validate_helpdesk_settings(values):
    categories = {
        value
        for value, _label in _parse_helpdesk_options(
            values.get("helpdesk_category_options"),
            field_name="helpdesk_category_options",
        )
    }
    _parse_helpdesk_options(
        values.get("helpdesk_status_labels"),
        field_name="helpdesk_status_labels",
        allowed_values=set(HELPDESK_STATUS_ORDER),
    )
    unknown_categories = sorted(
        {
            rule["category"]
            for rule in _parse_helpdesk_assignment_rules(
                values.get("helpdesk_assignment_rules")
            )
            if rule["category"] not in categories
        }
    )
    if unknown_categories:
        raise ValidationError(
            {
                "helpdesk_assignment_rules": (
                    "Assignment rule category must exist in ticket categories: "
                    f"{', '.join(unknown_categories)}."
                )
            }
        )


def helpdesk_settings(values=None):
    values = values or all_settings()
    return deepcopy(values["helpdesk"])


def helpdesk_label(values=None):
    settings = helpdesk_settings(values)
    return str(settings.get("helpdesk_display_label") or "Service Desk").strip() or "Service Desk"


def helpdesk_reference_prefix(values=None):
    settings = helpdesk_settings(values)
    return _reference_prefix(settings.get("helpdesk_reference_prefix"), "SD")


def helpdesk_reference(ticket_id, values=None):
    prefix = helpdesk_reference_prefix(values)
    separator = "" if prefix.endswith(("-", "_")) else "-"
    try:
        normalized_id = f"{int(ticket_id):05d}"
    except (TypeError, ValueError):
        normalized_id = str(ticket_id or "NEW")
    return f"{prefix}{separator}{normalized_id}"


def helpdesk_category_options(values=None):
    settings = helpdesk_settings(values)
    return [
        {"value": value, "label": label}
        for value, label in _safe_helpdesk_options(
            settings.get("helpdesk_category_options"),
            field_name="helpdesk_category_options",
            fallback=HELPDESK_DEFAULT_CATEGORY_OPTIONS,
        )
    ]


def helpdesk_category_label(category, values=None):
    options = {
        option["value"]: option["label"]
        for option in helpdesk_category_options(values)
    }
    fallback = _helpdesk_default_option_map(HELPDESK_DEFAULT_CATEGORY_OPTIONS)
    category_key = str(category or "").strip()
    return (
        options.get(category_key)
        or fallback.get(category_key)
        or category_key.replace("_", " ").replace("-", " ").title()
    )


def helpdesk_status_labels(values=None):
    settings = helpdesk_settings(values)
    labels = _helpdesk_default_option_map(HELPDESK_DEFAULT_STATUS_LABELS)
    labels.update(
        _safe_helpdesk_options(
            settings.get("helpdesk_status_labels"),
            field_name="helpdesk_status_labels",
            fallback=HELPDESK_DEFAULT_STATUS_LABELS,
            allowed_values=set(HELPDESK_STATUS_ORDER),
        )
    )
    return labels


def helpdesk_status_options(values=None):
    labels = helpdesk_status_labels(values)
    return [
        {"value": status, "label": labels.get(status, status.replace("_", " ").title())}
        for status in HELPDESK_STATUS_ORDER
    ]


def helpdesk_status_label(status, values=None):
    labels = helpdesk_status_labels(values)
    status_key = str(status or "").strip()
    return labels.get(status_key, status_key.replace("_", " ").title())


def helpdesk_assignment_rules(values=None):
    settings = helpdesk_settings(values)
    try:
        rules = _parse_helpdesk_assignment_rules(
            settings.get("helpdesk_assignment_rules")
        )
    except ValidationError:
        rules = []
    return {rule["category"]: rule for rule in rules}


def helpdesk_assignment_rule(category, values=None):
    return helpdesk_assignment_rules(values).get(str(category or "").strip())


def application_number_prefix():
    return _reference_prefix(
        setting_value("workflow", "default_application_number_prefix"),
        "APP",
    )


def payment_reference_prefix():
    return _reference_prefix(
        setting_value("workflow", "payment_reference_prefix"),
        "PORTAL",
    )


def password_policy_errors(password):
    security = all_settings()["security"]
    max_length = min(int(security.get("password_max_length", 20)), 20)
    min_length = min(int(security["password_min_length"]), max_length)
    errors = []
    if len(password) < min_length:
        errors.append(
            f"Password must contain at least {min_length} characters."
        )
    if len(password) > max_length:
        errors.append(f"Password must contain {max_length} characters or fewer.")
    if security["password_require_uppercase"] and not any(character.isupper() for character in password):
        errors.append("Password must contain at least one uppercase character.")
    if security["password_require_number"] and not any(character.isdigit() for character in password):
        errors.append("Password must contain at least one number.")
    return errors


def invalidate_settings_cache():
    cache.delete(CACHE_KEY)


def _normalize_leave_approval_roles(value):
    allowed = {"teacher", "dean"}
    roles = []
    for item in str(value or "").replace("\n", ",").split(","):
        role = item.strip().lower()
        if not role:
            continue
        if role not in allowed:
            raise ValidationError(
                {"leave_approval_roles": "Use only teacher and dean approval roles."}
            )
        if role not in roles:
            roles.append(role)
    if not roles:
        raise ValidationError({"leave_approval_roles": "Select at least one approval role."})
    return ",".join(roles)


def _normalize_identifier_csv(value, field_name):
    identifiers = [
        item.strip().lower()
        for item in str(value or "").replace("\n", ",").split(",")
        if item.strip()
    ]
    if any(len(item) > 80 for item in identifiers):
        raise ValidationError({field_name: "Identifiers must be 80 characters or fewer."})
    return ",".join(dict.fromkeys(identifiers))


def _split_credit_limit_rule(line):
    for separator in ("|", ","):
        parts = [part.strip() for part in line.split(separator)]
        if len(parts) == 3:
            return parts
    parts = [part.strip() for part in line.split(":")]
    if len(parts) >= 3:
        return [":".join(parts[:-2]), parts[-2], parts[-1]]
    return None


def _normalize_registration_credit_limit_overrides(value):
    normalized_lines = []
    for raw_line in str(value or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = _split_credit_limit_rule(line)
        if not parts:
            raise ValidationError(
                {
                    "registration_credit_limit_overrides": (
                        "Use one rule per line in the form scope,min,max."
                    )
                }
            )
        scope, minimum, maximum = parts
        try:
            minimum_value = int(minimum)
            maximum_value = int(maximum)
        except (TypeError, ValueError):
            raise ValidationError(
                {"registration_credit_limit_overrides": "Credit limits must be whole numbers."}
            ) from None
        if not scope or minimum_value < 0 or maximum_value < 1 or minimum_value > maximum_value:
            raise ValidationError(
                {
                    "registration_credit_limit_overrides": (
                        "Each rule needs a scope and a valid minimum/maximum range."
                    )
                }
            )
        normalized_lines.append(f"{scope.strip()},{minimum_value},{maximum_value}")
    return "\n".join(normalized_lines)


def _normalize_value(name, value, config):
    field_type = config["type"]
    if field_type == "boolean":
        if not isinstance(value, bool):
            raise ValidationError({name: "Provide true or false."})
        return value
    if field_type == "number":
        if isinstance(value, bool):
            raise ValidationError({name: "Provide a valid number."})
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise ValidationError({name: "Provide a valid whole number."}) from None
        if "min" in config and normalized < config["min"]:
            raise ValidationError({name: f"Must be at least {config['min']}."})
        if "max" in config and normalized > config["max"]:
            raise ValidationError({name: f"Must be at most {config['max']}."})
        return normalized

    normalized = str(value or "").strip()
    if config.get("required", True) and not normalized:
        raise ValidationError({name: "This field is required."})
    if config.get("max_length") and len(normalized) > config["max_length"]:
        raise ValidationError({name: f"Must be {config['max_length']} characters or fewer."})
    if name == "monthly_allowance_amount":
        try:
            amount = Decimal(normalized)
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError({name: "Provide a valid currency amount."}) from None
        if amount < 0:
            raise ValidationError({name: "Amount cannot be negative."})
        if amount > Decimal("999999.99"):
            raise ValidationError({name: "Amount must be 999999.99 or less."})
        return f"{amount:.2f}"
    if name in {"eligible_enrollment_statuses", "ineligible_enrollment_status_markers"}:
        items = [item.strip().lower() for item in normalized.split(",") if item.strip()]
        return ",".join(dict.fromkeys(items))
    if name in {"eligible_program_codes", "eligible_cohort_codes"}:
        items = [item.strip().upper() for item in normalized.split(",") if item.strip()]
        return ",".join(dict.fromkeys(items))
    if name == "registration_credit_limit_overrides":
        return _normalize_registration_credit_limit_overrides(normalized)
    if name == "leave_approval_roles":
        return _normalize_leave_approval_roles(normalized)
    if name == "leave_dean_approver_identifiers":
        return _normalize_identifier_csv(normalized, name)
    if name in {"timezone", "allowance_reset_timezone"} and normalized:
        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError:
            raise ValidationError({name: "Use a valid IANA timezone such as UTC or America/New_York."}) from None
    if name == "currency_code" and normalized:
        normalized = normalized.upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValidationError({name: "Use a three-letter ISO 4217 currency code such as USD."})
    if name in {"default_application_number_prefix", "payment_reference_prefix", "helpdesk_reference_prefix"} and normalized:
        normalized = _reference_prefix(normalized, "")
        if not normalized:
            raise ValidationError({name: "Use letters, numbers, hyphens, or underscores."})
    if name == "helpdesk_category_options":
        return _normalize_helpdesk_options(
            normalized,
            field_name="helpdesk_category_options",
        )
    if name == "helpdesk_status_labels":
        return _normalize_helpdesk_options(
            normalized,
            field_name="helpdesk_status_labels",
            allowed_values=set(HELPDESK_STATUS_ORDER),
        )
    if name == "helpdesk_assignment_rules":
        return _normalize_helpdesk_assignment_rules(normalized)
    if name == "venue_category_options":
        return _normalize_venue_category_options(normalized)
    if name == "requester_roles":
        return _normalize_venue_requester_roles(normalized)
    if name == "blackout_dates":
        return _normalize_venue_blackout_dates(normalized)
    if name in {"required_fields_event", "required_fields_personal"}:
        return _normalize_venue_required_fields(normalized, field_name=name)
    if name == "residence_type_options":
        return _normalize_hostel_residence_type_options(normalized)
    if name == "room_code_format":
        _validate_hostel_room_code_format(normalized)
        return normalized
    if name.endswith("_enabled_modules"):
        modules = [
            item.strip().lower()
            for item in normalized.split(",")
            if item.strip()
        ]
        unknown = sorted(set(modules) - set(OPTIONAL_FEATURES))
        if unknown:
            raise ValidationError(
                {name: f"Unknown module key(s): {', '.join(unknown)}."}
            )
        normalized = ",".join(dict.fromkeys(modules))
    if name.endswith("_code") and normalized:
        normalized = normalized.upper()
    if field_type == "email" and normalized:
        try:
            validate_email(normalized)
        except ValidationError:
            raise ValidationError({name: "Provide a valid email address."}) from None
    choices = {choice["value"] for choice in config.get("choices", [])}
    if choices and normalized not in choices:
        raise ValidationError({name: "Select a valid option."})
    if field_type in {"url", "image"} and normalized:
        if normalized.startswith("/") and not normalized.startswith("//"):
            return normalized
        try:
            URLValidator(schemes=["http", "https"])(normalized)
        except ValidationError:
            raise ValidationError({name: "Use a valid https:// URL or a site-relative path such as /images/logo.png."}) from None
    if field_type == "color" and normalized:
        if normalized.lower() == "currentcolor":
            normalized = "#000000"
        if not normalized.startswith("#") or len(normalized) not in {4, 7}:
            raise ValidationError({name: "Use a hex color such as #0f766e."})
        hex_digits = normalized[1:]
        if any(character not in "0123456789abcdefABCDEF" for character in hex_digits):
            raise ValidationError({name: "Use a hex color such as #0f766e."})
        return normalized.lower()
    if name in {"applicant_allowed_file_extensions", "default_allowed_file_extensions"} and normalized:
        extensions = [item.strip().lower().lstrip(".") for item in normalized.split(",") if item.strip()]
        if not extensions or any(not item.isalnum() for item in extensions):
            raise ValidationError({name: "Use comma-separated file extensions such as pdf,jpg,png."})
        normalized = ",".join(dict.fromkeys(extensions))
    return normalized


def validate_section_values(section, submitted, current):
    if section not in SETTINGS_SECTIONS:
        raise ValidationError({"section": "Unknown settings section."})
    if not isinstance(submitted, dict):
        raise ValidationError({"values": "Settings values must be an object."})

    fields = SETTINGS_SECTIONS[section]["fields"]
    unknown = sorted(set(submitted) - set(fields))
    if unknown:
        raise ValidationError({"values": f"Unknown setting(s): {', '.join(unknown)}."})

    normalized = dict(current)
    for name, value in submitted.items():
        normalized[name] = _normalize_value(name, value, fields[name])

    if section == "academic" and normalized["registration_min_credit_hours"] > normalized["registration_max_credit_hours"]:
        raise ValidationError(
            {"registration_max_credit_hours": "Maximum registration credits must be at least the minimum."}
        )
    if section == "helpdesk":
        _validate_helpdesk_settings(normalized)
    if section == "venue_booking_policy":
        _validate_venue_booking_policy_settings(normalized)
    if section == "hostel_policy":
        _validate_hostel_policy_settings(normalized)
    return normalized


def section_payload(section, values, record=None):
    definition = SETTINGS_SECTIONS[section]
    return {
        "key": section,
        "title": definition["title"],
        "description": definition["description"],
        "fields": [
            {"key": key, **deepcopy(config)}
            for key, config in definition["fields"].items()
        ],
        "values": deepcopy(values),
        "updated_at": record.updated_at.isoformat() if record else None,
        "updated_by": (
            record.updated_by.user.get_full_name().strip()
            or record.updated_by.user.username
            if record and record.updated_by_id
            else ""
        ),
    }


def feature_flags(values=None):
    values = values or all_settings()
    dashboard = values["dashboard"]
    librarian_library = values.get("librarian_library", {})
    flags = {
        feature: bool(dashboard.get(field_name, True))
        for feature, field_name in OPTIONAL_FEATURES.items()
    }
    # Librarian-controlled library sub-features override the admin dashboard defaults
    flags["library_laptops"] = bool(librarian_library.get("laptops_enabled", flags.get("library_laptops", True)))
    flags["library_rooms"] = bool(librarian_library.get("rooms_enabled", flags.get("library_rooms", True)))
    return flags


def _csv_items(value):
    return [
        item.strip().lower()
        for item in str(value or "").split(",")
        if item.strip()
    ]


def role_settings(values=None):
    values = values or all_settings()
    roles = values.get("roles", {})
    return {
        role: {
            "label": roles.get(f"{role}_label") or defaults["label"],
            "short_label": roles.get(f"{role}_short_label") or defaults["short_label"],
            "description": roles.get(f"{role}_description") or defaults["description"],
        }
        for role, defaults in CORE_ROLE_DEFAULTS.items()
    }


def module_labels(values=None):
    values = values or all_settings()
    roles = values.get("roles", {})
    return {
        module: roles.get(f"module_{module}_label") or label
        for module, label in MODULE_LABEL_DEFAULTS.items()
    }


def dining_label(values=None):
    return module_labels(values).get("canteen") or MODULE_LABEL_DEFAULTS["canteen"]


def venue_booking_label(values=None):
    return module_labels(values).get("venue_booking") or MODULE_LABEL_DEFAULTS["venue_booking"]


def canteen_policy_settings(values=None):
    values = values or all_settings()
    return deepcopy(values["canteen_policy"])


def canteen_policy_public_payload(values=None):
    values = values or all_settings()
    return {
        **canteen_policy_settings(values),
        "enabled": feature_flags(values).get("canteen", True),
        "label": dining_label(values),
    }


def venue_booking_policy_settings(values=None):
    values = values or all_settings()
    return deepcopy(values["venue_booking_policy"])


def venue_category_options(values=None):
    settings = venue_booking_policy_settings(values)
    return [
        {"value": value, "label": label}
        for value, label in _safe_helpdesk_options(
            settings.get("venue_category_options"),
            field_name="venue_category_options",
            fallback=VENUE_BOOKING_DEFAULT_CATEGORY_OPTIONS,
            key_max_length=40,
            label_max_length=80,
        )
    ]


def venue_category_values(values=None):
    return {option["value"] for option in venue_category_options(values)}


def venue_category_label(category, values=None):
    labels = {
        option["value"]: option["label"]
        for option in venue_category_options(values)
    }
    category_key = str(category or "").strip().lower()
    return (
        labels.get(category_key)
        or category_key.replace("_", " ").replace("-", " ").title()
        or "Uncategorized"
    )


def venue_booking_requester_roles(values=None):
    settings = venue_booking_policy_settings(values)
    roles = _csv_items(settings.get("requester_roles"))
    return [
        role
        for role in dict.fromkeys(roles or VENUE_BOOKING_REQUESTER_ROLES)
        if role in VENUE_BOOKING_REQUESTER_ROLES
    ]


def venue_booking_required_fields(booking_type, values=None):
    settings = venue_booking_policy_settings(values)
    field_name = (
        "required_fields_personal"
        if str(booking_type or "").strip().lower() == "personal"
        else "required_fields_event"
    )
    fields = _csv_items(settings.get(field_name))
    return [
        item
        for item in dict.fromkeys(fields)
        if item in VENUE_BOOKING_REQUIRED_FIELD_CHOICES
    ]


def venue_booking_blackout_ranges(values=None):
    settings = venue_booking_policy_settings(values)
    try:
        return _parse_venue_blackout_ranges(settings.get("blackout_dates"))
    except ValidationError:
        return []


def venue_booking_is_blackout_date(booking_date, values=None):
    return any(
        start <= booking_date <= end
        for start, end in venue_booking_blackout_ranges(values)
    )


def venue_booking_policy_payload(values=None):
    values = values or all_settings()
    settings = venue_booking_policy_settings(values)
    return {
        **settings,
        "enabled": feature_flags(values).get("venue_booking", True),
        "label": venue_booking_label(values),
        "venue_categories": venue_category_options(values),
        "requester_roles": venue_booking_requester_roles(values),
        "reviewer_roles": deepcopy(VENUE_BOOKING_REVIEWER_ROLE_CHOICES),
        "approval_modes": deepcopy(VENUE_BOOKING_APPROVAL_MODE_CHOICES),
        "required_fields": {
            "event": venue_booking_required_fields("event", values),
            "personal": venue_booking_required_fields("personal", values),
        },
        "blackout_ranges": [
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
            for start, end in venue_booking_blackout_ranges(values)
        ],
    }


def hostel_policy_settings(values=None):
    values = values or all_settings()
    return deepcopy(values["hostel_policy"])


def hostel_residence_type_options(values=None):
    settings = hostel_policy_settings(values)
    return [
        {"value": value, "label": label}
        for value, label in _safe_helpdesk_options(
            settings.get("residence_type_options"),
            field_name="residence_type_options",
            fallback=HOSTEL_DEFAULT_RESIDENCE_TYPE_OPTIONS,
            key_max_length=10,
            label_max_length=80,
        )
    ]


def hostel_residence_type_values(values=None):
    return {option["value"] for option in hostel_residence_type_options(values)}


def hostel_residence_type_label(hostel_type, values=None):
    labels = {
        option["value"]: option["label"]
        for option in hostel_residence_type_options(values)
    }
    hostel_type_key = str(hostel_type or "").strip().lower()
    return (
        labels.get(hostel_type_key)
        or hostel_type_key.replace("_", " ").replace("-", " ").title()
    )


def _hostel_code_token(value):
    return "".join(
        character.upper() if character.isalnum() else "-"
        for character in str(value or "").strip()
    ).strip("-")


def _hostel_floor_token(value, *, padded):
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        number = int(raw)
    except (TypeError, ValueError):
        return raw.upper()
    return f"{number:02d}" if padded else str(number)


def _hostel_room_token(value, *, padded):
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.isdigit():
        return raw.zfill(2) if padded else raw
    return raw.upper()


def normalize_hostel_room_code(value):
    normalized = "".join(
        character.upper() if character.isalnum() else character if character in {"-", "_"} else "-"
        for character in str(value or "").strip()
    )
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-_")[:80]


def hostel_room_code(hostel_code, floor, room_number, values=None):
    settings = hostel_policy_settings(values)
    template = (
        str(settings.get("room_code_format") or "").strip()
        or HOSTEL_DEFAULT_ROOM_CODE_FORMAT
    )
    tokens = {
        "hostel": _hostel_code_token(hostel_code),
        "hostel_lower": _hostel_code_token(hostel_code).lower(),
        "floor": _hostel_floor_token(floor, padded=True),
        "floor_raw": _hostel_floor_token(floor, padded=False),
        "room": _hostel_room_token(room_number, padded=True),
        "room_raw": _hostel_room_token(room_number, padded=False),
    }
    try:
        rendered = template.format(**tokens)
    except (KeyError, ValueError):
        rendered = HOSTEL_DEFAULT_ROOM_CODE_FORMAT.format(**tokens)
    return normalize_hostel_room_code(rendered)


def hostel_policy_payload(values=None):
    settings = hostel_policy_settings(values)
    return {
        **settings,
        "residence_types": hostel_residence_type_options(values),
        "bed_assignment_rules": deepcopy(HOSTEL_BED_ASSIGNMENT_RULE_CHOICES),
    }


def role_module_permissions(values=None):
    values = values or all_settings()
    roles = values.get("roles", {})
    permissions = {}
    valid_modules = set(OPTIONAL_FEATURES)
    for role, defaults in ROLE_MODULE_DEFAULTS.items():
        configured = _csv_items(
            roles.get(f"{role}_enabled_modules", _csv_default(defaults))
        )
        permissions[role] = [
            module
            for module in dict.fromkeys(configured or defaults)
            if module in valid_modules
        ]
    return permissions


def role_module_enabled(role, module, values=None):
    permissions = role_module_permissions(values)
    if role not in permissions:
        return True
    return module in permissions[role]


def feature_enabled(feature):
    return feature_flags().get(feature, True)


def maintenance_mode_enabled():
    return bool(setting_value("security", "maintenance_mode"))


def features_enabled_for_path(path, role=None):
    values = all_settings()
    path_text = str(path or "").lower()
    parts = {part for part in str(path or "").split("/") if part}
    flags = feature_flags(values)
    permissions = role_module_permissions(values) if role else {}

    def allowed(feature):
        return flags.get(feature, True) and (
            not role or feature in permissions.get(role, tuple(OPTIONAL_FEATURES))
        )

    library_settings = values.get("librarian_library", {})
    if (
        (
            "/student/library/books" in path_text
            or "/student/library/book-requests" in path_text
            or "/librarian/books" in path_text
            or "/librarian/book-requests" in path_text
        )
        and not bool(library_settings.get("books_enabled", True))
    ):
        return False
    if (
        ("/student/library/laptops" in path_text or "/librarian/laptops" in path_text)
        and not allowed("library_laptops")
    ):
        return False
    if (
        ("/student/library/rooms" in path_text or "/librarian/rooms" in path_text)
        and not allowed("library_rooms")
    ):
        return False

    for path_part, feature_keys in FEATURE_PATH_SETTINGS.items():
        if path_part not in parts:
            continue
        enabled = any(
            allowed(feature)
            for feature in feature_keys
        )
        if not enabled:
            return False
    return True


def _ui_customization_values():
    try:
        record = SystemSetting.objects.get(key=setting_key("ui_customization"))
        if isinstance(record.value, dict):
            return {
                key: record.value.get(key, default)
                for key, default in UI_CUSTOMIZATION_DEFAULTS.items()
            }
    except SystemSetting.DoesNotExist:
        pass
    return dict(UI_CUSTOMIZATION_DEFAULTS)


SETUP_REQUIRED_FIELDS = [
    {
        "section": "university",
        "field": "university_name",
        "label": "University name",
        "placeholder_values": {"Your University"},
    },
    {
        "section": "university",
        "field": "short_name",
        "label": "Short name",
        "placeholder_values": {"UNI"},
    },
    {
        "section": "university",
        "field": "legal_name",
        "label": "Legal name",
        "placeholder_values": {"Your University"},
    },
    {
        "section": "university",
        "field": "tagline",
        "label": "Tagline",
        "placeholder_values": {"Configurable university portal"},
    },
    {
        "section": "university",
        "field": "address",
        "label": "Address",
        "placeholder_values": {"University address"},
    },
    {
        "section": "university",
        "field": "phone",
        "label": "Main phone",
        "placeholder_values": {"+00 000 000 0000"},
    },
    {
        "section": "university",
        "field": "email",
        "label": "Main email",
        "placeholder_values": {"info@example.edu"},
    },
    {
        "section": "university",
        "field": "admissions_email",
        "label": "Admissions email",
        "placeholder_values": {"admissions@example.edu"},
    },
    {
        "section": "localization",
        "field": "timezone",
        "label": "Timezone",
    },
    {
        "section": "localization",
        "field": "locale",
        "label": "Locale",
    },
    {
        "section": "localization",
        "field": "currency_code",
        "label": "Currency code",
    },
    {
        "section": "workflow",
        "field": "default_application_number_prefix",
        "label": "Application number prefix",
    },
]


def setup_completeness_payload(values=None):
    values = values or all_settings()
    items = []
    for item in SETUP_REQUIRED_FIELDS:
        value = values.get(item["section"], {}).get(item["field"], "")
        text_value = str(value or "").strip()
        placeholders = item.get("placeholder_values", set())
        complete = bool(text_value) and text_value not in placeholders
        items.append(
            {
                "key": f"{item['section']}.{item['field']}",
                "section": item["section"],
                "field": item["field"],
                "label": item["label"],
                "complete": complete,
            }
        )
    completed = sum(1 for item in items if item["complete"])
    return {
        "complete": completed == len(items),
        "completed": completed,
        "total": len(items),
        "items": items,
    }


def public_settings_payload():
    values = all_settings()
    university = values["university"]
    localization = values["localization"]
    terminology = terminology_settings()
    academic = values["academic"]
    workflow = values["workflow"]
    ui_customization = _ui_customization_values()
    ui_customization["accent_color"] = ui_customization.get("accent_color", "#0f766e")
    security = values["security"]
    dashboard_features = feature_flags(values)
    library_settings = values.get("librarian_library", {})
    return {
        "maintenance": {
            "enabled": bool(security["maintenance_mode"]),
        },
        "general": {
            "portal_name": values["general"]["ums_name"],
            "support_email": values["general"]["support_email"],
            "support_phone": values["general"]["support_phone"],
            "maintenance_banner": values["general"]["maintenance_banner"],
        },
        "university": {
            "name": university["university_name"],
            "short_name": university["short_name"],
            "legal_name": university["legal_name"],
            "tagline": university["tagline"],
            "description": university["description"],
            "address": university["address"],
            "phone": university["phone"],
            "email": university["email"],
            "admissions_email": university["admissions_email"],
            "website_url": university["website_url"],
            "logo_url": university["logo_url"],
            "public_hero_image_url": university["public_hero_image_url"],
            "social_image_url": university["social_image_url"],
            "login_image_url": university["login_image_url"],
            "favicon_url": university["favicon_url"],
        },
        "localization": {
            "timezone": localization["timezone"],
            "locale": localization["locale"],
            "currency_code": localization["currency_code"],
            "currency_symbol": localization["currency_symbol"],
            "number_format": localization["number_format"],
            "date_format": localization["date_format"],
            "time_format": localization["time_format"],
        },
        "terminology": terminology,
        "branding": {
            "primary_color": ui_customization.get("button_color", "#18181b"),
            "secondary_color": ui_customization.get("secondary_button_color", "#f4f4f5"),
            "accent_color": ui_customization.get("accent_color", "#0f766e"),
            "logo_url": university["logo_url"] or ui_customization.get("logo_url", ""),
            "public_hero_image_url": university["public_hero_image_url"],
            "login_image_url": university["login_image_url"],
            "favicon_url": university["favicon_url"],
            "social_image_url": university["social_image_url"],
        },
        "policies": {
            "password": {
                "min_length": security["password_min_length"],
                "max_length": security["password_max_length"],
                "require_uppercase": security["password_require_uppercase"],
                "require_number": security["password_require_number"],
            },
            "uploads": {
                "default_limit_mb": workflow["default_upload_limit_mb"],
                "default_allowed_file_extensions": workflow["default_allowed_file_extensions"],
                "applicant_max_upload_mb": workflow["applicant_max_upload_mb"],
                "applicant_allowed_file_extensions": workflow["applicant_allowed_file_extensions"],
            },
            "attendance_threshold_percent": academic["attendance_threshold_percent"],
            "leave_notice_period_days": workflow["leave_request_min_notice_days"],
            "default_academic_calendar_type": academic["default_academic_calendar_type"],
            "default_application_number_prefix": workflow["default_application_number_prefix"],
            "default_payment_gateway_provider": workflow["default_payment_gateway_provider"],
            "payment_reference_prefix": workflow["payment_reference_prefix"],
            "venue_booking": venue_booking_policy_payload(values),
            "dining": canteen_policy_public_payload(values),
        },
        "ui_customization": {
            "brand_name": ui_customization.get("brand_name", ""),
            "sidebar_label": ui_customization.get("sidebar_label", ""),
            "logo_url": ui_customization.get("logo_url", ""),
            "logo_alt_text": ui_customization.get("logo_alt_text", ""),
            "default_avatar_url": ui_customization.get("default_avatar_url", ""),
            "loading_spinner": ui_customization.get("loading_spinner", "dna"),
            "loading_spinner_size": ui_customization.get("loading_spinner_size", 80),
            "card_density": ui_customization.get("card_density", ""),
            "show_scope_badge": ui_customization.get("show_scope_badge", True),
            "show_link_descriptions": ui_customization.get("show_link_descriptions", True),
            "primary_text_color": ui_customization.get("primary_text_color", ""),
            "secondary_text_color": ui_customization.get("secondary_text_color", ""),
            "accent_color": ui_customization.get("accent_color", ""),
            "background_color": ui_customization.get("background_color", ""),
            "font_family": ui_customization.get("font_family", ""),
            "font_size_base": ui_customization.get("font_size_base", ""),
            "dashboard_background_image_url": ui_customization.get("dashboard_background_image_url", ""),
            "button_color": ui_customization.get("button_color", ""),
            "button_text_color": ui_customization.get("button_text_color", ""),
            "secondary_button_color": ui_customization.get("secondary_button_color", ""),
            "secondary_button_text_color": ui_customization.get("secondary_button_text_color", ""),
            "button_border_radius": ui_customization.get("button_border_radius", ""),
            "icon_color": ui_customization.get("icon_color", ""),
            "icon_size": ui_customization.get("icon_size", ""),
            "dark_primary_text_color": ui_customization.get("dark_primary_text_color", ""),
            "dark_secondary_text_color": ui_customization.get("dark_secondary_text_color", ""),
            "dark_background_color": ui_customization.get("dark_background_color", ""),
            "dark_button_color": ui_customization.get("dark_button_color", ""),
            "dark_button_text_color": ui_customization.get("dark_button_text_color", ""),
            "dark_secondary_button_color": ui_customization.get("dark_secondary_button_color", ""),
            "dark_secondary_button_text_color": ui_customization.get("dark_secondary_button_text_color", ""),
            "dark_accent_color": ui_customization.get("dark_accent_color", ""),
            "dark_icon_color": ui_customization.get("dark_icon_color", ""),
            "sidebar_font_size": ui_customization.get("sidebar_font_size", ""),
            "sidebar_font_weight": ui_customization.get("sidebar_font_weight", ""),
            "sidebar_icon_size": ui_customization.get("sidebar_icon_size", ""),
            "sidebar_width": ui_customization.get("sidebar_width", "16rem"),
            "sidebar_collapsed_by_default": ui_customization.get("sidebar_collapsed_by_default", False),
            "sticky_header": ui_customization.get("sticky_header", True),
            "show_breadcrumbs": ui_customization.get("show_breadcrumbs", True),
            "show_footer": ui_customization.get("show_footer", True),
            "card_border_radius": ui_customization.get("card_border_radius", "0.75rem"),
            "card_shadow": ui_customization.get("card_shadow", "default"),
            "card_background_color": ui_customization.get("card_background_color", ""),
            "avatar_shape": ui_customization.get("avatar_shape", "circle"),
            "avatar_size": ui_customization.get("avatar_size", "md"),
            "table_stripe_color": ui_customization.get("table_stripe_color", ""),
            "modal_overlay_opacity": ui_customization.get("modal_overlay_opacity", 50),
        },
        "features": dashboard_features,
        "roles": role_settings(values),
        "module_labels": module_labels(values),
        "module_permissions": role_module_permissions(values),
        "library_services": {
            "books_enabled": bool(library_settings.get("books_enabled", True)),
            "laptops_enabled": bool(library_settings.get("laptops_enabled", True)),
            "rooms_enabled": bool(library_settings.get("rooms_enabled", True)),
        },
        "setup": setup_completeness_payload(values),
    }
