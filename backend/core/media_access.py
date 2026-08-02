from pathlib import PurePosixPath
from urllib.parse import quote, unquote

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.signing import BadSignature, dumps, loads
from django.http import Http404, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


PROFILE_PICTURE_PREFIX = "profile-pictures/"
PROFILE_PICTURE_SALT = "portal.profile-picture"
INTERNAL_MEDIA_PREFIX = "/_protected_media/"

PUBLIC_DIRECT_PREFIXES = (
    "settings/images/",
)


def protected_media_url(name):
    if not name:
        return None
    return f"/ums-auth/backend{settings.MEDIA_URL}{quote(name.lstrip('/'), safe='/')}"


def public_profile_picture_url(profile, request=None):
    if not profile or not getattr(profile, "profile_picture", None):
        return None
    token = dumps({"profile": profile.pk}, salt=PROFILE_PICTURE_SALT)
    url = f"{settings.MEDIA_URL}{PROFILE_PICTURE_PREFIX}{token}"
    return request.build_absolute_uri(url) if request else url


@api_view(["GET", "HEAD"])
@permission_classes([AllowAny])
def protected_media(request, path):
    clean_path = _clean_path(path)
    if not clean_path:
        raise Http404

    media_path, cache_control = _authorized_media_path(request, clean_path)
    if not media_path or not default_storage.exists(media_path):
        raise Http404

    response = HttpResponse()
    response["X-Accel-Redirect"] = f"{INTERNAL_MEDIA_PREFIX}{quote(media_path, safe='/')}"
    response["Cache-Control"] = cache_control
    response["X-Content-Type-Options"] = "nosniff"
    return response


def _clean_path(path):
    decoded = unquote(str(path or "")).replace("\\", "/").lstrip("/")
    pure_path = PurePosixPath(decoded)
    if pure_path.is_absolute() or any(part in {"", ".", ".."} for part in pure_path.parts):
        return ""
    return pure_path.as_posix()


def _authorized_media_path(request, path):
    if path.startswith(PROFILE_PICTURE_PREFIX):
        return _profile_picture_path(path), "public, max-age=3600"

    if path.startswith("profiles/pictures/"):
        return None, ""

    if path.startswith(PUBLIC_DIRECT_PREFIXES):
        return path, "public, max-age=604800"

    if path.startswith("public/news/"):
        return _public_news_path(request, path), "public, max-age=604800"

    profile = _request_profile(request)
    if not profile:
        return None, ""

    if _is_admin(profile):
        return path, "private, no-store"

    checks = (
        _applicant_document_allowed,
        _attendance_certificate_allowed,
        _leave_attachment_allowed,
        _exam_slip_allowed,
        _course_resource_allowed,
        _study_guide_allowed,
        _assignment_attachment_allowed,
        _hr_document_allowed,
        _election_photo_allowed,
    )
    for check in checks:
        if check(profile, path):
            return path, "private, no-store"
    return None, ""


def _request_profile(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_active:
        return None
    from auth_app.models import Profile

    return Profile.objects.filter(user=user).select_related("user").first()


def _is_admin(profile):
    return profile.role == profile.ROLE_ADMIN or profile.user.is_staff or profile.user.is_superuser


def _is_executive(profile):
    return profile.role == profile.ROLE_EXECUTIVE


def _profile_picture_path(path):
    token = path[len(PROFILE_PICTURE_PREFIX) :].strip("/")
    try:
        payload = loads(token, salt=PROFILE_PICTURE_SALT)
    except (BadSignature, TypeError, ValueError):
        return None

    from auth_app.models import Profile

    profile = (
        Profile.objects.filter(pk=payload.get("profile"))
        .exclude(profile_picture="")
        .first()
    )
    if not profile or not profile.profile_picture:
        return None
    return profile.profile_picture.name


def _public_news_path(request, path):
    from home_app.models import PublicNews

    if PublicNews.objects.filter(image=path, status=PublicNews.STATUS_PUBLISHED).exists():
        return path
    profile = _request_profile(request)
    if profile and _is_admin(profile):
        return path
    return None


def _applicant_document_allowed(profile, path):
    if not path.startswith("applications/"):
        return False
    from applicant_app.models import ApplicationDocument

    document = (
        ApplicationDocument.objects.select_related("application__applicant__profile")
        .filter(file=path)
        .first()
    )
    if not document:
        return False
    return (
        document.application.applicant.profile_id == profile.id
        or _is_executive(profile)
    )


def _attendance_certificate_allowed(profile, path):
    if not path.startswith("attendance/medical-certificates/"):
        return False
    from student_app.models import AttendanceRecord

    record = (
        AttendanceRecord.objects.select_related("student", "offering__instructor", "marked_by")
        .filter(medical_certificate=path)
        .first()
    )
    if not record:
        return False
    return profile.id in {
        record.student_id,
        record.marked_by_id,
        record.offering.instructor_id,
    }


def _leave_attachment_allowed(profile, path):
    if not path.startswith("leave/attachments/"):
        return False
    from student_app.models import LeaveRequest

    leave_request = (
        LeaveRequest.objects.select_related("student", "reviewed_by")
        .filter(attachment=path)
        .first()
    )
    if not leave_request:
        return False
    return profile.id in {leave_request.student_id, leave_request.reviewed_by_id}


def _exam_slip_allowed(profile, path):
    if not path.startswith("academic/exam-slips/"):
        return False
    from student_app.models import ExamSlip

    slip = ExamSlip.objects.filter(file=path).first()
    return bool(slip and slip.student_id == profile.id)


def _course_resource_allowed(profile, path):
    if not path.startswith("courses/resources/"):
        return False
    from student_app.models import Enrollment
    from teacher_app.models import CourseResource

    resource = CourseResource.objects.select_related("offering").filter(file=path).first()
    if not resource:
        return False
    if resource.offering.instructor_id == profile.id:
        return True
    if profile.role != profile.ROLE_STUDENT or not resource.is_published:
        return False
    return Enrollment.objects.filter(
        student=profile,
        offering=resource.offering,
        completed_at__isnull=True,
    ).exists()


def _study_guide_allowed(profile, path):
    if not path.startswith("study-guides/"):
        return False
    from admin_app.models import CourseOffering
    from student_app.models import Enrollment

    offering = CourseOffering.objects.filter(study_guide=path).first()
    if not offering:
        return False
    if offering.instructor_id == profile.id:
        return True
    if profile.role != profile.ROLE_STUDENT:
        return False
    return Enrollment.objects.filter(
        student=profile,
        offering=offering,
        completed_at__isnull=True,
    ).exists()


def _assignment_attachment_allowed(profile, path):
    if not path.startswith("assignments/attachments/"):
        return False
    from teacher_app.models import AssignmentAttachment, AssignmentGroupMembership

    attachment = (
        AssignmentAttachment.objects.select_related(
            "submission__student",
            "submission__assignment",
            "submission__assignment__offering",
        )
        .filter(file=path)
        .first()
    )
    if not attachment:
        return False

    submission = attachment.submission
    if profile.id == submission.student_id:
        return True
    if profile.id == submission.assignment.offering.instructor_id:
        return True
    if submission.assignment_group_id:
        return AssignmentGroupMembership.objects.filter(
            group_id=submission.assignment_group_id,
            student=profile,
        ).exists()
    return False


def _hr_document_allowed(profile, path):
    if not path.startswith("hr/employee-documents/"):
        return False
    from hr_app.models import EmployeeDocument

    document = EmployeeDocument.objects.select_related("employee__profile").filter(file=path).first()
    if not document:
        return False
    return profile.role == profile.ROLE_HR or document.employee.profile_id == profile.id


def _election_photo_allowed(profile, path):
    if not path.startswith("elections/candidates/"):
        return False
    from technician_app.models import ElectionCandidate

    candidate = ElectionCandidate.objects.filter(photo=path).first()
    return bool(candidate and candidate.status == candidate.STATUS_APPROVED)
