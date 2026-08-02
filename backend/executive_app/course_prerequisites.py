from admin_app import models
from executive_app.course_schedule import courses_for_scope


def prerequisite_options(scope, *, exclude_course=None):
    courses = courses_for_scope(scope).filter(is_active=True).order_by("code")
    if exclude_course:
        courses = courses.exclude(pk=exclude_course.pk)
    return courses


def _creates_cycle(course, prerequisites):
    pending_ids = set(prerequisites.values_list("id", flat=True))
    visited = set()

    while pending_ids:
        candidate_id = pending_ids.pop()
        if candidate_id == course.id:
            return True
        if candidate_id in visited:
            continue
        visited.add(candidate_id)
        pending_ids.update(
            prerequisite_id
            for prerequisite_id in models.Course.objects.filter(pk=candidate_id).values_list(
                "prerequisites__id",
                flat=True,
            )
            if prerequisite_id
        )

    return False


def resolve_prerequisites(scope, raw_ids, *, course=None):
    if raw_ids in (None, ""):
        raw_ids = []
    if not isinstance(raw_ids, list):
        return None, "Prerequisites must be provided as a list of course IDs."

    try:
        prerequisite_ids = {int(course_id) for course_id in raw_ids}
    except (TypeError, ValueError):
        return None, "Select valid prerequisite courses."

    if course and course.id in prerequisite_ids:
        return None, "A course cannot be its own prerequisite."

    prerequisites = prerequisite_options(scope, exclude_course=course).filter(pk__in=prerequisite_ids)
    if prerequisites.count() != len(prerequisite_ids):
        return None, "Select valid active prerequisite courses from your assigned scope."
    if course and _creates_cycle(course, prerequisites):
        return None, "Prerequisites cannot create a circular course requirement."

    return prerequisites, None
