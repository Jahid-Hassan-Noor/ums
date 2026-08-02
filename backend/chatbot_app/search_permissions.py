from django.apps import apps
from django.db.models import Q

from admin_app.models import CourseOffering, Profile
from chatbot_app.models import SearchDocument
from student_app.models import Enrollment
from teacher_app.assignment_service import teacher_offerings


FORBIDDEN_DOMAINS = {
    "applicant_document",
    "audit",
    "gradebook",
    "grades",
    "marks",
    "payment_details",
    "payment_secret",
    "private_helpdesk",
    "results",
    "scholarship_document",
    "submission",
}

FORBIDDEN_DOCUMENT_TYPES = {
    "applicant_private_document",
    "assignment_submission",
    "audit_log",
    "gpa",
    "grade",
    "helpdesk_private_body",
    "mark",
    "medical_certificate",
    "passport",
    "payment_gateway_key",
    "payment_secret",
    "private_media",
    "result_detail",
    "scholarship_file",
    "staff_note",
}

STAFF_ROLES = {
    Profile.ROLE_ADMIN,
    Profile.ROLE_EXECUTIVE,
    Profile.ROLE_LIBRARIAN,
    Profile.ROLE_CATERER,
    Profile.ROLE_TECHNICIAN,
    Profile.ROLE_ACCOUNTANT,
    Profile.ROLE_TEACHER,
}


def profile_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return (
        Profile.objects.select_related("user")
        .filter(user=user, is_active=True)
        .first()
    )


def role_for_user(user):
    profile = profile_for_user(user)
    return profile.role if profile else ""


def is_admin_user(user, profile=None):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = profile or profile_for_user(user)
    return bool(profile and profile.role == Profile.ROLE_ADMIN)


def is_forbidden_document(document):
    metadata = document.safe_metadata or {}
    return (
        document.domain in FORBIDDEN_DOMAINS
        or document.document_type in FORBIDDEN_DOCUMENT_TYPES
        or metadata.get("sensitive") is True
    )


def base_visibility_filter(user):
    visibility_filter = Q(visibility=SearchDocument.VISIBILITY_PUBLIC)
    if not user or not user.is_authenticated:
        return visibility_filter
    if is_admin_user(user):
        return Q()
    return visibility_filter | Q(
        visibility__in=[
            SearchDocument.VISIBILITY_AUTHENTICATED,
            SearchDocument.VISIBILITY_ROLE_BASED,
            SearchDocument.VISIBILITY_OWNER_ONLY,
            SearchDocument.VISIBILITY_COURSE_MEMBER,
            SearchDocument.VISIBILITY_TEACHER_ASSIGNED,
            SearchDocument.VISIBILITY_EXECUTIVE_SCOPE,
            SearchDocument.VISIBILITY_STAFF_SCOPE,
        ]
    )


def _student_has_course_access(profile, document):
    if not profile or profile.role != Profile.ROLE_STUDENT:
        return False
    queryset = Enrollment.objects.filter(student=profile, completed_at__isnull=True)
    if document.course_offering_id:
        return queryset.filter(offering_id=document.course_offering_id).exists()
    if document.course_id:
        return queryset.filter(offering__course_id=document.course_id).exists()
    return False


def _teacher_has_course_access(profile, document):
    if not profile or profile.role != Profile.ROLE_TEACHER:
        return False
    offerings = teacher_offerings(profile, include_inactive=True)
    if document.course_offering_id:
        return offerings.filter(pk=document.course_offering_id).exists()
    if document.course_id:
        return offerings.filter(course_id=document.course_id).exists()
    return False


def _executive_scope_matches(profile, document):
    if not profile or profile.role != Profile.ROLE_EXECUTIVE:
        return False
    scoped_fields = (
        "school_id",
        "center_id",
        "department_id",
        "unit_id",
        "program_id",
    )
    has_scope = any(getattr(document, field) for field in scoped_fields)
    if not has_scope:
        return False
    return any(
        getattr(document, field) and getattr(document, field) == getattr(profile, field)
        for field in scoped_fields
    )


def _role_allowed(profile, document):
    allowed_roles = set(document.allowed_roles or [])
    return bool(profile and profile.role in allowed_roles)


def has_index_access(user, document):
    if not document.is_active or is_forbidden_document(document):
        return False

    visibility = document.visibility
    profile = profile_for_user(user)
    if visibility == SearchDocument.VISIBILITY_PUBLIC:
        return True
    if not user or not user.is_authenticated or not profile:
        return False
    if is_admin_user(user, profile):
        return True
    if visibility == SearchDocument.VISIBILITY_AUTHENTICATED:
        return True
    if visibility == SearchDocument.VISIBILITY_ROLE_BASED:
        return _role_allowed(profile, document)
    if visibility == SearchDocument.VISIBILITY_OWNER_ONLY:
        return document.owner_user_id == user.id
    if visibility == SearchDocument.VISIBILITY_COURSE_MEMBER:
        return (
            _student_has_course_access(profile, document)
            or _teacher_has_course_access(profile, document)
        )
    if visibility == SearchDocument.VISIBILITY_TEACHER_ASSIGNED:
        return _teacher_has_course_access(profile, document)
    if visibility == SearchDocument.VISIBILITY_EXECUTIVE_SCOPE:
        return _executive_scope_matches(profile, document)
    if visibility == SearchDocument.VISIBILITY_STAFF_SCOPE:
        return profile.role in STAFF_ROLES
    if visibility == SearchDocument.VISIBILITY_ADMIN_ONLY:
        return False
    return False


def source_object_for_document(document):
    if not (
        document.source_app_label
        and document.source_model
        and document.source_object_id
    ):
        return None
    try:
        model = apps.get_model(document.source_app_label, document.source_model)
    except LookupError:
        return None
    try:
        return model._default_manager.get(pk=document.source_object_id)
    except model.DoesNotExist:
        return None


def source_object_is_available(document):
    if not (
        document.source_app_label
        and document.source_model
        and document.source_object_id
    ):
        return True

    source = source_object_for_document(document)
    if source is None:
        return False
    if hasattr(source, "is_active") and source.is_active is False:
        return False
    if hasattr(source, "is_published") and source.is_published is False:
        return False
    status = getattr(source, "status", "")
    if status in {"archived", "cancelled", "draft", "rejected"}:
        return False
    return True


def course_offering_scope(offering_id):
    if not offering_id:
        return {}
    offering = (
        CourseOffering.objects.select_related(
            "course",
            "course__school",
            "course__center",
            "course__department",
            "course__program",
            "semester",
        )
        .filter(pk=offering_id)
        .first()
    )
    if not offering:
        return {}
    return {
        "course_id": offering.course_id,
        "course_offering_id": offering.id,
        "semester_id": offering.semester_id,
        "school_id": offering.course.school_id,
        "center_id": offering.course.center_id,
        "department_id": offering.course.department_id,
        "program_id": offering.course.program_id,
    }
