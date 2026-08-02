from copy import deepcopy

from django.core.cache import cache
from django.core.validators import URLValidator, validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q

from admin_app.models import SystemSetting


CACHE_KEY = "ums.system_settings.v1"
SETTINGS_KEY_PREFIX = "ums."
LEGACY_SETTINGS_KEY_PREFIX = "portal."


OPTIONAL_FEATURES = {
    "venue_booking": "enable_venue_booking",
    "canteen": "enable_canteen",
    "library": "enable_library",
    "library_laptops": "enable_library_laptops",
    "library_rooms": "enable_library_rooms",
    "ict_helpdesk": "enable_ict_helpdesk",
    "hostel": "enable_hostel",
    "elections": "enable_elections",
    "fines": "enable_fines",
    "quizzes": "enable_quizzes",
}


FEATURE_PATH_SETTINGS = {
    "elections": ("elections",),
    "venue-bookings": ("venue_booking",),
    "venues": ("venue_booking",),
    "canteen": ("canteen",),
    "caterer": ("canteen",),
    "library": ("library",),
    "librarian": ("library",),
    "library-laptops": ("library", "library_laptops"),
    "library-rooms": ("library", "library_rooms"),
    "ict-helpdesk": ("ict_helpdesk",),
    "helpdesk": ("ict_helpdesk",),
    "hostels": ("hostel",),
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


def field(label, default, field_type="text", **options):
    return {
        "label": label,
        "default": default,
        "type": field_type,
        **options,
    }


SETTINGS_SECTIONS = {
    "general": {
        "title": "General UMS Settings",
        "description": "Platform identity, support contacts, localization, and UMS-wide messaging.",
        "fields": {
            "ums_name": field("UMS name", "University Management System", max_length=120),
            "support_email": field("Support email", "support@example.edu", "email"),
            "support_phone": field("Support phone", "+604 774 7300", "tel", max_length=40),
            "timezone": field(
                "Default timezone",
                "Asia/Kuala_Lumpur",
                "select",
                choices=[
                    {"value": "Asia/Kuala_Lumpur", "label": "Asia/Kuala Lumpur"},
                    {"value": "UTC", "label": "UTC"},
                ],
            ),
            "date_format": field(
                "Date format",
                "DD/MM/YYYY",
                "select",
                choices=[
                    {"value": "DD/MM/YYYY", "label": "DD/MM/YYYY"},
                    {"value": "MM/DD/YYYY", "label": "MM/DD/YYYY"},
                    {"value": "YYYY-MM-DD", "label": "YYYY-MM-DD"},
                ],
            ),
            "default_language": field(
                "Default language",
                "en",
                "select",
                choices=[
                    {"value": "en", "label": "English"},
                    {"value": "ms", "label": "Bahasa Melayu"},
                ],
            ),
            "maintenance_banner": field(
                "UMS banner message",
                "",
                "textarea",
                required=False,
                max_length=500,
                help_text="Shown as a UMS-wide operational announcement when supported by the client.",
            ),
        },
    },
    "university": {
        "title": "University Profile",
        "description": "Public university identity, contact details, and brand images shown across the site.",
        "fields": {
            "university_name": field("University name", "Your University", max_length=180),
            "short_name": field("Short name", "UMS", max_length=40),
            "legal_name": field("Legal name", "Your University", max_length=220),
            "tagline": field("Tagline", "University Management System", max_length=160),
            "description": field(
                "Public description",
                "A configurable university profile powered by UMS.",
                "textarea",
                max_length=800,
            ),
            "address": field("Address", "University address", "textarea", max_length=500),
            "phone": field("Main phone", "+604 774 7300", "tel", max_length=40),
            "email": field("Main email", "info@example.edu", "email"),
            "admissions_email": field("Admissions email", "admissions@example.edu", "email"),
            "website_url": field("Website URL", "https://example.edu", "url", required=False, max_length=500),
            "logo_url": field("Logo image", "/images/ums/ums-logo.svg", "image", required=False, max_length=500),
            "public_hero_image_url": field(
                "Default public hero image",
                "/images/login_image.jpg",
                "image",
                required=False,
                max_length=500,
            ),
            "social_image_url": field(
                "Default social image",
                "/images/login_image.jpg",
                "image",
                required=False,
                max_length=500,
            ),
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
        "description": "Default timing, approval, export, and upload rules for UMS workflows.",
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
        },
    },
    "notifications": {
        "title": "Notifications",
        "description": "Control which workflow events create notifications and how UMS messages are identified.",
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
            "sender_display_name": field("Sender display name", "UMS", max_length=120),
        },
    },
    "dashboard": {
        "title": "Customize UMS Features",
        "description": "Enable or disable optional UMS features.",
        "fields": {
            "enable_venue_booking": field("Enable venue booking", True, "boolean", high_impact=True),
            "enable_canteen": field("Enable canteen", True, "boolean", high_impact=True),
            "enable_library": field("Enable library", True, "boolean", high_impact=True),
            "enable_library_laptops": field("Enable library laptop borrowing", True, "boolean", high_impact=True),
            "enable_library_rooms": field("Enable library discussion room booking", True, "boolean", high_impact=True),
            "enable_ict_helpdesk": field("Enable ICT helpdesk", True, "boolean", high_impact=True),
            "enable_hostel": field("Enable hostel management", True, "boolean", high_impact=True),
            "enable_elections": field("Enable elections", True, "boolean", high_impact=True),
            "enable_fines": field("Enable fines and charges", True, "boolean", high_impact=True),
            "enable_quizzes": field("Enable quizzes", True, "boolean", high_impact=True),
        },
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
    "librarian_library": {
        "title": "Library Service Settings",
        "description": "Control which library services are available to students. Managed by librarians.",
        "fields": {
            "books_enabled": field("Enable book borrowing", True, "boolean"),
            "laptops_enabled": field("Enable laptop borrowing", True, "boolean"),
            "rooms_enabled": field("Enable discussion room booking", True, "boolean"),
        },
    },
}


UI_CUSTOMIZATION_DEFINITION = {
    "title": "UMS UI Customization",
    "description": "Customize UI appearance, colors, fonts, and backgrounds across the site.",
    "fields": {
        "brand_name": field("Dashboard brand name", "University Management System", max_length=140),
        "sidebar_label": field("Sidebar brand label", "University Management System", max_length=140),
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
    if name == "applicant_allowed_file_extensions" and normalized:
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


def feature_flags():
    dashboard = all_settings()["dashboard"]
    librarian_library = all_settings().get("librarian_library", {})
    flags = {
        feature: bool(dashboard.get(field_name, True))
        for feature, field_name in OPTIONAL_FEATURES.items()
    }
    # Librarian-controlled library sub-features override the admin dashboard defaults
    flags["library_laptops"] = bool(librarian_library.get("laptops_enabled", flags.get("library_laptops", True)))
    flags["library_rooms"] = bool(librarian_library.get("rooms_enabled", flags.get("library_rooms", True)))
    return flags


def feature_enabled(feature):
    return feature_flags().get(feature, True)


def maintenance_mode_enabled():
    return bool(setting_value("security", "maintenance_mode"))


def features_enabled_for_path(path):
    parts = {part for part in str(path or "").split("/") if part}
    flags = feature_flags()
    for path_part, feature_keys in FEATURE_PATH_SETTINGS.items():
        if path_part in parts and not any(flags.get(feature, True) for feature in feature_keys):
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


def public_settings_payload():
    values = all_settings()
    university = values["university"]
    ui_customization = _ui_customization_values()
    security = values["security"]
    return {
        "maintenance": {
            "enabled": bool(security["maintenance_mode"]),
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
        "features": feature_flags(),
        "library_services": {
            "books_enabled": bool(all_settings().get("librarian_library", {}).get("books_enabled", True)),
            "laptops_enabled": bool(all_settings().get("librarian_library", {}).get("laptops_enabled", True)),
            "rooms_enabled": bool(all_settings().get("librarian_library", {}).get("rooms_enabled", True)),
        },
    }
