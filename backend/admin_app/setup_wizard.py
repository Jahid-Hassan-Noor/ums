from admin_app import models
from admin_app.role_config import ROLE_OWNER_SETTINGS
from admin_app.settings_registry import (
    SETTINGS_SECTIONS,
    UI_CUSTOMIZATION_DEFAULTS,
    all_settings,
    feature_flags,
    invalidate_settings_cache,
    setting_key,
    setup_completeness_payload,
)
from applicant_app import models as applicant_models
from applicant_app.admissions_setup import admissions_setup
from home_app import models as public_models


SETUP_STEP_KEYS = [
    "institution_profile",
    "branding",
    "localization",
    "terminology",
    "academic_structure",
    "academic_calendars",
    "enabled_modules",
    "role_ownership",
    "admissions",
    "public_website",
]


ROADMAP_MODULES = {
    "admissions": "Admissions",
    "finance": "Finance",
    "canteen": "Dining/canteen",
    "library": "Library",
    "hostel": "Hostel",
    "ict_helpdesk": "Helpdesk",
    "elections": "Elections",
    "venue_booking": "Venue booking",
}


def _item(
    key,
    label,
    complete,
    *,
    detail="",
    href="",
    message="",
    required=True,
    section="",
    field="",
):
    return {
        "key": key,
        "label": label,
        "complete": bool(complete),
        "required": bool(required),
        "detail": str(detail or ""),
        "href": str(href or ""),
        "message": str(message or ""),
        "section": str(section or ""),
        "field": str(field or ""),
    }


def _step(
    key,
    title,
    description,
    items,
    *,
    href="",
    actions=None,
    settings_sections=None,
):
    required_items = [item for item in items if item["required"]]
    completed = sum(1 for item in required_items if item["complete"])
    total = len(required_items)
    complete = completed == total
    return {
        "key": key,
        "title": title,
        "description": description,
        "complete": complete,
        "completed": completed,
        "total": total,
        "href": href,
        "items": items,
        "actions": actions or [],
        "settings_sections": settings_sections or [],
    }


def _setting_items(checklist, section, step_key=None):
    step_key = step_key or section
    return [
        _item(
            item["key"],
            item["label"],
            item["complete"],
            href=f"/admin/setup-wizard?step={step_key}",
            message=f"Update {item['label'].lower()} in the setup wizard.",
            section=item["section"],
            field=item["field"],
        )
        for item in checklist["items"]
        if item["section"] == section
    ]


def _text_complete(value, placeholders=None):
    text = str(value or "").strip()
    return bool(text) and text not in (placeholders or set())


def _count_item(key, label, count, href, message, *, required=True):
    return _item(
        key,
        label,
        count > 0,
        detail=f"{count} configured",
        href=href,
        message=message,
        required=required,
    )


def _active_profile_exists(role):
    return models.Profile.objects.filter(
        role=role,
        is_active=True,
        user__is_active=True,
    ).exists()


def _active_code_exists(model, code):
    code = str(code or "").strip()
    return bool(code) and model.objects.filter(code__iexact=code, is_active=True).exists()


def _fresh_settings_values(values=None):
    if values is None:
        values = all_settings()
    if any(section not in values for section in SETTINGS_SECTIONS):
        invalidate_settings_cache()
        values = all_settings()
    return values


def _ui_customization_values():
    defaults = dict(UI_CUSTOMIZATION_DEFAULTS)
    record = models.SystemSetting.objects.filter(
        key=setting_key("ui_customization")
    ).first()
    if record and isinstance(record.value, dict):
        defaults.update(
            {
                key: record.value.get(key, default)
                for key, default in UI_CUSTOMIZATION_DEFAULTS.items()
            }
        )
    return defaults


def _configured_owner_exists(role, values):
    config = ROLE_OWNER_SETTINGS.get(role, {})
    role_values = values.get("roles", {})
    checks = [
        (models.Unit, role_values.get(config.get("unit_code"))),
        (models.Center, role_values.get(config.get("center_code"))),
        (models.Department, role_values.get(config.get("department_code"))),
    ]
    return any(_active_code_exists(model, code) for model, code in checks if code)


def _module_owner_item(values, flags, feature, role, label, href):
    if not flags.get(feature, True):
        return _item(
            f"role_ownership.{feature}",
            label,
            True,
            detail="Module disabled",
            href=href,
            message="",
            required=False,
        )
    owner_exists = _configured_owner_exists(role, values) or _active_profile_exists(role)
    return _item(
        f"role_ownership.{feature}",
        label,
        owner_exists,
        detail="Configured" if owner_exists else "No owner found",
        href=href,
        message=f"Configure {label.lower()} before enabling this workflow for users.",
    )


def _settings_section(section, fields):
    return {"section": section, "fields": list(fields)}


def _institution_profile_step(values, checklist):
    return _step(
        "institution_profile",
        "Institution Profile",
        "Name, legal identity, contact details, and website basics.",
        _setting_items(checklist, "university", "institution_profile"),
        href="/admin/settings",
        actions=[{"label": "Open settings", "href": "/admin/settings"}],
        settings_sections=[
            _settings_section(
                "university",
                [
                    "university_name",
                    "short_name",
                    "legal_name",
                    "tagline",
                    "description",
                    "address",
                    "phone",
                    "email",
                    "admissions_email",
                    "website_url",
                ],
            )
        ],
    )


def _branding_step(values):
    university = values["university"]
    ui_customization = _ui_customization_values()
    primary_color = ui_customization.get("button_color") or "#18181b"
    items = [
        _item(
            "branding.logo",
            "Logo image",
            _text_complete(university.get("logo_url"), {"/images/ums/ums-logo.svg"}),
            detail=university.get("logo_url") or "Missing",
            href="/admin/setup-wizard?step=branding",
            message="Add an institution logo URL or upload one from portal settings.",
            section="university",
            field="logo_url",
        ),
        _item(
            "branding.favicon",
            "Favicon",
            _text_complete(university.get("favicon_url")),
            detail=university.get("favicon_url") or "Missing",
            href="/admin/setup-wizard?step=branding",
            message="Add a favicon for browser tabs and saved shortcuts.",
            section="university",
            field="favicon_url",
        ),
        _item(
            "branding.hero_image",
            "Public hero image",
            _text_complete(university.get("public_hero_image_url")),
            detail=university.get("public_hero_image_url") or "Missing",
            href="/admin/setup-wizard?step=branding",
            message="Set a default public hero image for pages without their own media.",
            section="university",
            field="public_hero_image_url",
        ),
        _item(
            "branding.primary_color",
            "Primary brand color",
            _text_complete(primary_color),
            detail=primary_color or "Missing",
            href="/admin/ui-customization",
            message="Choose primary brand colors in UI customization.",
        ),
    ]
    return _step(
        "branding",
        "Branding",
        "Logo, favicon, public hero image, and brand colors.",
        items,
        href="/admin/ui-customization",
        actions=[
            {"label": "Open UI customization", "href": "/admin/ui-customization"},
            {"label": "Open portal settings", "href": "/admin/settings"},
        ],
        settings_sections=[
            _settings_section(
                "university",
                ["logo_url", "favicon_url", "public_hero_image_url", "social_image_url", "login_image_url"],
            )
        ],
    )


def _localization_step(values, checklist):
    setting_items = _setting_items(checklist, "localization")
    localization = values["localization"]
    extra_items = [
        _item(
            "localization.date_format",
            "Date format",
            _text_complete(localization.get("date_format")),
            detail=localization.get("date_format"),
            href="/admin/setup-wizard?step=localization",
            message="Choose the default date format for admin and public displays.",
            section="localization",
            field="date_format",
        ),
        _item(
            "localization.time_format",
            "Time format",
            _text_complete(localization.get("time_format")),
            detail=localization.get("time_format"),
            href="/admin/setup-wizard?step=localization",
            message="Choose the default time format for schedules and deadlines.",
            section="localization",
            field="time_format",
        ),
    ]
    return _step(
        "localization",
        "Localization",
        "Timezone, locale, currency, and date/time formats.",
        setting_items + extra_items,
        href="/admin/settings",
        actions=[{"label": "Open settings", "href": "/admin/settings"}],
        settings_sections=[
            _settings_section(
                "localization",
                [
                    "timezone",
                    "locale",
                    "currency_code",
                    "currency_symbol",
                    "number_format",
                    "date_format",
                    "time_format",
                ],
            )
        ],
    )


def _terminology_step(values):
    terminology = values["terminology"]
    fields = [
        ("school_label", "School label"),
        ("center_label", "Center label"),
        ("program_label", "Program/programme label"),
        ("semester_label", "Semester/session label"),
        ("academic_year_label", "Academic year label"),
    ]
    items = [
        _item(
            f"terminology.{field}",
            label,
            _text_complete(terminology.get(field)),
            detail=terminology.get(field),
            href="/admin/setup-wizard?step=terminology",
            message=f"Set the {label.lower()} for this institution.",
            section="terminology",
            field=field,
        )
        for field, label in fields
    ]
    return _step(
        "terminology",
        "Terminology",
        "Institution-specific labels for academic structure and sessions.",
        items,
        href="/admin/settings",
        actions=[{"label": "Open settings", "href": "/admin/settings"}],
        settings_sections=[
            _settings_section(
                "terminology",
                [
                    "school_label",
                    "center_label",
                    "department_label",
                    "unit_label",
                    "program_label",
                    "course_label",
                    "semester_label",
                    "academic_year_label",
                    "student_id_label",
                    "staff_id_label",
                    "applicant_label",
                ],
            )
        ],
    )


def _academic_structure_step():
    active_schools = models.School.objects.filter(is_active=True).count()
    active_centers = models.Center.objects.filter(is_active=True).count()
    active_departments = models.Department.objects.filter(is_active=True).count()
    active_units = models.Unit.objects.filter(is_active=True).count()
    active_programs = models.Program.objects.filter(is_active=True).count()
    items = [
        _item(
            "academic_structure.school_or_center",
            "School or academic center",
            active_schools + active_centers > 0,
            detail=f"{active_schools} schools, {active_centers} centers",
            href="/admin/academics",
            message="Create at least one school or academic center.",
        ),
        _item(
            "academic_structure.department_or_unit",
            "Department or unit",
            active_departments + active_units > 0,
            detail=f"{active_departments} departments, {active_units} units",
            href="/admin/academics/departments",
            message="Create departments or units for academic and operational ownership.",
        ),
        _count_item(
            "academic_structure.programs",
            "Programs",
            active_programs,
            "/admin/academics/programmes",
            "Create at least one program or programme.",
        ),
    ]
    return _step(
        "academic_structure",
        "Academic Structure",
        "Schools, centers, departments, units, and programs.",
        items,
        href="/admin/academics",
        actions=[
            {"label": "Schools", "href": "/admin/schools"},
            {"label": "Centres", "href": "/admin/centres"},
            {"label": "Departments", "href": "/admin/academics/departments"},
            {"label": "Units", "href": "/admin/academics/units"},
            {"label": "Programmes", "href": "/admin/academics/programmes"},
        ],
    )


def _academic_calendars_step():
    semester_configurations = models.SemesterConfiguration.objects.count()
    semester_plans = models.Semester.objects.count()
    active_semesters = models.Semester.objects.filter(is_active=True).count()
    active_sessions = models.AcademicSession.objects.filter(is_active=True).count()
    whole_year_centers = models.Center.objects.filter(
        center_type=models.Center.CENTER_ACADEMIC,
        academic_calendar_mode=models.Center.CALENDAR_WHOLE_YEAR,
        is_active=True,
    ).count()
    items = [
        _count_item(
            "academic_calendars.semester_groups",
            "Semester group definitions",
            semester_configurations,
            "/admin/semesters",
            "Configure semester groups and their length patterns.",
        ),
        _item(
            "academic_calendars.semester_plans",
            "Semester plans",
            semester_plans > 0 or whole_year_centers > 0,
            detail=f"{semester_plans} semester plans",
            href="/admin/semesters",
            message="Create at least one semester plan for semester-based calendars.",
        ),
        _item(
            "academic_calendars.active_periods",
            "Active academic periods",
            active_semesters + active_sessions > 0,
            detail=f"{active_semesters} active semesters, {active_sessions} active sessions",
            href="/admin/semesters",
            message="Start a semester or create an active whole-year session.",
        ),
    ]
    return _step(
        "academic_calendars",
        "Academic Calendars",
        "Semester groups, whole-year sessions, and active periods.",
        items,
        href="/admin/semesters",
        actions=[{"label": "Open academic calendar", "href": "/admin/semesters"}],
    )


def _enabled_modules_step(values):
    flags = feature_flags(values)
    items = [
        _item(
            f"enabled_modules.{feature}",
            label,
            isinstance(flags.get(feature), bool),
            detail="Enabled" if flags.get(feature, True) else "Disabled",
            href="/admin/setup-wizard?step=enabled_modules",
            message=f"Choose whether {label.lower()} should be enabled.",
            section="dashboard",
            field=f"enable_{feature}",
        )
        for feature, label in ROADMAP_MODULES.items()
    ]
    return _step(
        "enabled_modules",
        "Enabled Modules",
        "Admissions, finance, dining, library, hostel, helpdesk, elections, and venue booking.",
        items,
        href="/admin/settings",
        actions=[{"label": "Open settings", "href": "/admin/settings"}],
        settings_sections=[
            _settings_section(
                "dashboard",
                [
                    "enable_admissions",
                    "enable_finance",
                    "enable_canteen",
                    "enable_library",
                    "enable_hostel",
                    "enable_ict_helpdesk",
                    "enable_elections",
                    "enable_venue_booking",
                ],
            )
        ],
    )


def _role_ownership_step(values):
    flags = feature_flags(values)
    items = [
        _module_owner_item(
            values,
            flags,
            "library",
            models.Profile.ROLE_LIBRARIAN,
            "Library owner",
            "/admin/setup-wizard?step=role_ownership",
        ),
        _module_owner_item(
            values,
            flags,
            "canteen",
            models.Profile.ROLE_CATERER,
            "Dining/canteen owner",
            "/admin/setup-wizard?step=role_ownership",
        ),
        _module_owner_item(
            values,
            flags,
            "ict_helpdesk",
            models.Profile.ROLE_TECHNICIAN,
            "Helpdesk owner",
            "/admin/setup-wizard?step=role_ownership",
        ),
        _item(
            "role_ownership.finance",
            "Finance owner",
            True if not flags.get("finance", True) else _active_profile_exists(models.Profile.ROLE_ACCOUNTANT),
            detail=(
                "Module disabled"
                if not flags.get("finance", True)
                else "Configured"
                if _active_profile_exists(models.Profile.ROLE_ACCOUNTANT)
                else "No active accountant found"
            ),
            href="/admin/manage/accountants",
            message="Create or activate at least one accountant account.",
            required=flags.get("finance", True),
        ),
        _item(
            "role_ownership.academic_executives",
            "Academic executive owners",
            _active_profile_exists(models.Profile.ROLE_EXECUTIVE),
            detail="Configured" if _active_profile_exists(models.Profile.ROLE_EXECUTIVE) else "No active executive found",
            href="/admin/manage/executives",
            message="Create or activate at least one executive account.",
        ),
    ]
    return _step(
        "role_ownership",
        "Role Ownership",
        "Owners for library, dining, helpdesk, finance, and academic executive work.",
        items,
        href="/admin/settings",
        actions=[
            {"label": "Role settings", "href": "/admin/settings"},
            {"label": "Create accounts", "href": "/admin/create-account"},
        ],
        settings_sections=[
            _settings_section(
                "roles",
                [
                    "librarian_default_center_code",
                    "librarian_default_unit_code",
                    "caterer_default_center_code",
                    "caterer_default_unit_code",
                    "technician_default_department_code",
                    "technician_default_unit_code",
                ],
            )
        ],
    )


def _admissions_step(values):
    flags = feature_flags(values)
    if not flags.get("admissions", True):
        return _step(
            "admissions",
            "Admissions",
            "Application prefix, required documents, workflow stages, and intake periods.",
            [
                _item(
                    "admissions.disabled",
                    "Admissions module decision",
                    True,
                    detail="Module disabled",
                    href="/admin/settings",
                    required=False,
                )
            ],
            href="/admin/manage/applicants/setup",
            actions=[{"label": "Enable admissions", "href": "/admin/settings"}],
        )

    setup = admissions_setup()
    prefix = setup.get("application_number_prefix") or values["workflow"].get(
        "default_application_number_prefix"
    )
    required_documents = setup.get("required_documents") or []
    enabled_steps = [
        item
        for item in setup.get("workflow_steps", [])
        if item.get("enabled")
    ]
    active_intakes = applicant_models.ApplicationIntake.objects.filter(is_active=True).count()
    items = [
        _item(
            "admissions.application_prefix",
            "Application prefix",
            _text_complete(prefix),
            detail=prefix or "Missing",
            href="/admin/setup-wizard?step=admissions",
            message="Set the admissions application number prefix.",
            section="workflow",
            field="default_application_number_prefix",
        ),
        _item(
            "admissions.required_documents",
            "Required documents",
            len(required_documents) > 0,
            detail=f"{len(required_documents)} required",
            href="/admin/manage/applicants/setup",
            message="Choose which application documents are required.",
        ),
        _item(
            "admissions.workflow_stages",
            "Workflow stages",
            len(enabled_steps) > 0,
            detail=f"{len(enabled_steps)} enabled stages",
            href="/admin/manage/applicants/setup",
            message="Enable at least one admissions workflow stage.",
        ),
        _count_item(
            "admissions.intake_periods",
            "Active intake periods",
            active_intakes,
            "/admin/manage/applicants",
            "Create at least one active intake period.",
        ),
    ]
    return _step(
        "admissions",
        "Admissions",
        "Application prefix, required documents, workflow stages, and intake periods.",
        items,
        href="/admin/manage/applicants/setup",
        actions=[
            {"label": "Admissions setup", "href": "/admin/manage/applicants/setup"},
            {"label": "Applicant management", "href": "/admin/manage/applicants"},
        ],
        settings_sections=[
            _settings_section("workflow", ["default_application_number_prefix"])
        ],
    )


def _public_website_step(values):
    flags = feature_flags(values)
    if not flags.get("public_website", True):
        return _step(
            "public_website",
            "Public Website",
            "Home, about, admissions, academic pages, news, and events.",
            [
                _item(
                    "public_website.disabled",
                    "Public website module decision",
                    True,
                    detail="Module disabled",
                    href="/admin/settings",
                    required=False,
                )
            ],
            href="/admin/public-content",
            actions=[{"label": "Enable public website", "href": "/admin/settings"}],
        )

    required_sections = [
        (public_models.PublicPage.SECTION_HOME, "Home page"),
        (public_models.PublicPage.SECTION_ABOUT, "About page"),
        (public_models.PublicPage.SECTION_ADMISSIONS, "Admissions page"),
        (public_models.PublicPage.SECTION_ACADEMICS, "Academic pages"),
    ]
    published_sections = set(
        public_models.PublicPage.objects.filter(
            status=public_models.PublicPage.STATUS_PUBLISHED
        ).values_list("section", flat=True)
    )
    news_count = public_models.PublicNews.objects.filter(
        status=public_models.PublicNews.STATUS_PUBLISHED
    ).count()
    events_count = public_models.PublicEvent.objects.filter(
        status=public_models.PublicEvent.STATUS_PUBLISHED
    ).count()
    items = [
        _item(
            f"public_website.{section}",
            label,
            section in published_sections,
            href="/admin/public-content",
            message=f"Publish a {label.lower()} for the public website.",
        )
        for section, label in required_sections
    ]
    items.extend(
        [
            _item(
                "public_website.news_or_events",
                "News or events",
                news_count + events_count > 0,
                detail=f"{news_count} news, {events_count} events",
                href="/admin/public-content",
                message="Publish at least one news item or event.",
                required=False,
            ),
            _item(
                "public_website.fallback_safe",
                "Fallback-safe public settings",
                True,
                detail="Public settings payload includes defaults",
                href="/admin/settings",
                required=False,
            ),
        ]
    )
    return _step(
        "public_website",
        "Public Website",
        "Home, about, admissions, academic pages, news, and events.",
        items,
        href="/admin/public-content",
        actions=[
            {"label": "Public content", "href": "/admin/public-content"},
            {"label": "News", "href": "/admin/public-content/news"},
            {"label": "Events", "href": "/admin/public-content/events"},
        ],
    )


def setup_wizard_payload(values=None):
    values = _fresh_settings_values(values)
    checklist = setup_completeness_payload(values)
    steps = [
        _institution_profile_step(values, checklist),
        _branding_step(values),
        _localization_step(values, checklist),
        _terminology_step(values),
        _academic_structure_step(),
        _academic_calendars_step(),
        _enabled_modules_step(values),
        _role_ownership_step(values),
        _admissions_step(values),
        _public_website_step(values),
    ]
    messages = []
    for step in steps:
        for item in step["items"]:
            if item["required"] and not item["complete"]:
                messages.append(
                    {
                        "key": item["key"],
                        "step": step["key"],
                        "label": item["label"],
                        "message": item["message"] or f"{item['label']} is incomplete.",
                        "href": item["href"] or step["href"],
                        "severity": "warning",
                    }
                )

    completed_steps = sum(1 for step in steps if step["complete"])
    total_required_items = sum(step["total"] for step in steps)
    completed_required_items = sum(step["completed"] for step in steps)
    return {
        "title": "Universal Setup Wizard",
        "section": "admin",
        "summary": {
            "complete": completed_steps == len(steps),
            "completed_steps": completed_steps,
            "total_steps": len(steps),
            "completed_required_items": completed_required_items,
            "total_required_items": total_required_items,
            "missing_required_items": total_required_items - completed_required_items,
        },
        "setup_checklist": checklist,
        "steps": steps,
        "messages": messages,
    }
