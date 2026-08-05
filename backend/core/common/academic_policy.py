from decimal import Decimal, InvalidOperation

from admin_app.settings_registry import setting_value


def _text_setting(section, name, default=""):
    try:
        return str(setting_value(section, name) or default).strip()
    except KeyError:
        return default


def _int_setting(section, name, default=0):
    try:
        return int(setting_value(section, name))
    except (KeyError, TypeError, ValueError):
        return default


def _bool_setting(section, name, default=False):
    try:
        value = setting_value(section, name)
    except KeyError:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _csv_items(value):
    text = str(value or "").replace("\n", ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def attendance_qr_ttl_seconds():
    minutes = _int_setting("academic", "attendance_code_expiry_minutes", 1)
    return max(minutes, 1) * 60


def evaluation_activity_label():
    return _text_setting("academic", "evaluation_activity_label", "Course Evaluation")


def evaluation_template_defaults():
    label = evaluation_activity_label()
    return {
        "name": _text_setting(
            "academic",
            "evaluation_template_name",
            f"{label} Standard Template",
        ),
        "description": _text_setting(
            "academic",
            "evaluation_template_description",
            "Standard course-content and teaching evaluation template.",
        ),
    }


def evaluation_default_survey_title(offering):
    label = evaluation_activity_label()
    course = getattr(offering, "course", None)
    if not course:
        return label
    return f"{label}: {course.code} {course.title}".strip()


def evaluation_required_by_default():
    return _bool_setting("academic", "evaluation_required_by_default", True)


def evaluation_registration_gate_enabled():
    return _bool_setting("academic", "evaluation_registration_gate_enabled", True)


def registration_prerequisites_required():
    return _bool_setting("academic", "registration_enforce_prerequisites", True)


def registration_passed_course_retake_allowed():
    return _bool_setting("academic", "registration_allow_passed_course_retake", False)


def _registration_scope_keys(student=None, semester=None):
    keys = set()
    if semester and getattr(semester, "calendar_group", ""):
        group = str(semester.calendar_group).strip().lower()
        keys.update({group, f"calendar:{group}", f"calendar_group:{group}"})
    program = getattr(student, "program", None) if student else None
    if program and getattr(program, "code", ""):
        code = program.code.strip().lower()
        keys.update({code, f"program:{code}", f"programme:{code}"})
    school = (
        getattr(student, "school", None)
        or getattr(program, "school", None)
        if student
        else None
    )
    if school and getattr(school, "code", ""):
        code = school.code.strip().lower()
        keys.add(f"school:{code}")
    center = (
        getattr(student, "center", None)
        or getattr(program, "center", None)
        if student
        else None
    )
    if center and getattr(center, "code", ""):
        code = center.code.strip().lower()
        keys.update({f"center:{code}", f"centre:{code}"})
    return keys


def _split_credit_rule(line):
    for separator in ("|", ","):
        parts = [part.strip() for part in line.split(separator)]
        if len(parts) == 3:
            return parts
    parts = [part.strip() for part in line.split(":")]
    if len(parts) >= 3:
        return [":".join(parts[:-2]), parts[-2], parts[-1]]
    return None


def _parse_credit_pair(minimum, maximum):
    try:
        minimum_value = int(minimum)
        maximum_value = int(maximum)
    except (TypeError, ValueError):
        return None
    if minimum_value < 0 or maximum_value < 1 or minimum_value > maximum_value:
        return None
    return minimum_value, maximum_value


def registration_credit_policy(student=None, semester=None):
    default_minimum = _int_setting("academic", "registration_min_credit_hours", 0)
    default_maximum = _int_setting("academic", "registration_max_credit_hours", 21)
    semester_maximum = getattr(semester, "max_credit_hours", None)
    maximum = int(semester_maximum or default_maximum)
    source = "semester" if semester_maximum else "default"
    if semester_maximum:
        maximum = min(maximum, default_maximum)
        source = "semester" if int(semester_maximum) <= default_maximum else "default"
    policy = {
        "minimum": default_minimum,
        "maximum": maximum,
        "source": source,
    }

    scope_keys = _registration_scope_keys(student=student, semester=semester)
    raw_rules = _text_setting("academic", "registration_credit_limit_overrides", "")
    for raw_line in raw_rules.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = _split_credit_rule(line)
        if not parts:
            continue
        scope, minimum, maximum_value = parts
        if scope.strip().lower() not in scope_keys:
            continue
        parsed = _parse_credit_pair(minimum, maximum_value)
        if not parsed:
            continue
        return {
            "minimum": parsed[0],
            "maximum": parsed[1],
            "source": scope.strip(),
        }
    return policy


def leave_required_roles():
    allowed = {"teacher", "dean"}
    configured = _csv_items(_text_setting("workflow", "leave_approval_roles", "teacher,dean"))
    roles = []
    for role in configured:
        normalized = role.strip().lower()
        if normalized in allowed and normalized not in roles:
            roles.append(normalized)
    return roles or ["teacher", "dean"]


def leave_dean_approver_identifiers():
    return {
        item.lower()
        for item in _csv_items(
            _text_setting("workflow", "leave_dean_approver_identifiers", "")
        )
    }


def leave_approval_requires_sequence():
    return (
        _text_setting("workflow", "leave_approval_order", "parallel").lower()
        == "configured_sequence"
    )


def result_policy_labels():
    return {
        "grade_point": _text_setting("academic", "grade_point_label", "Grade Point"),
        "gpa": _text_setting("academic", "gpa_label", "GPA"),
        "cgpa": _text_setting("academic", "cgpa_label", "CGPA"),
        "grade_scale_heading": _text_setting("academic", "grade_scale_heading", "Grade Scale"),
        "grade_scale_description": _text_setting(
            "academic",
            "grade_scale_description",
            "Institutional grading scale used for grade point calculation.",
        ),
        "academic_standing_good": _text_setting(
            "academic",
            "academic_standing_good_label",
            "Good Standing",
        ),
        "academic_standing_probation": _text_setting(
            "academic",
            "academic_standing_probation_label",
            "Academic Probation",
        ),
    }


def academic_standing_label(cgpa):
    try:
        value = Decimal(str(cgpa or "0"))
    except (InvalidOperation, TypeError, ValueError):
        value = Decimal("0")
    threshold = Decimal(str(_int_setting("academic", "academic_standing_good_min_points", 2)))
    labels = result_policy_labels()
    if value >= threshold:
        return labels["academic_standing_good"]
    return labels["academic_standing_probation"]
