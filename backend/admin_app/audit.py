import json
import logging
import re

from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework.pagination import PageNumberPagination

from admin_app.models import AuditLog
from auth_app.models import Profile


logger = logging.getLogger(__name__)

MUTATING_METHODS = {
    "POST": "Created",
    "PUT": "Updated",
    "PATCH": "Updated",
    "DELETE": "Deleted",
}
AUDITED_PREFIXES = {
    "admin": Profile.ROLE_ADMIN,
    "executive": Profile.ROLE_EXECUTIVE,
}
SENSITIVE_FIELD_PARTS = {"password", "secret", "token", "authorization", "cookie"}
VIEW_AUDIT_DETAIL_FIELDS = {
    "changes",
    "high_impact",
    "new_value",
    "previous_value",
    "reason",
    "setting",
}


class AuditLogPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


def serialize_audit_log(log):
    account = log.user.user if log.user_id and log.user else None
    full_name = account.get_full_name().strip() if account else ""
    return {
        "id": log.id,
        "action": log.action,
        "object_type": log.object_type,
        "object_id": log.object_id,
        "details": log.details,
        "created_at": log.created_at.isoformat(),
        "actor": {
            "profile_id": log.user_id,
            "username": account.username if account else "",
            "email": account.email if account else "",
            "full_name": full_name or (account.username if account else "Unknown account"),
            "role": log.user.role if log.user_id and log.user else "",
        },
    }


def filter_audit_logs(queryset, params):
    search = params.get("search", "").strip()
    action = params.get("action", "").strip()
    actor = params.get("actor", "").strip()
    object_type = params.get("object_type", "").strip()
    category = params.get("category", "").strip()
    date_from = parse_date(params.get("date_from", "").strip())
    date_to = parse_date(params.get("date_to", "").strip())

    if search:
        queryset = queryset.filter(
            Q(action__icontains=search)
            | Q(object_type__icontains=search)
            | Q(object_id__icontains=search)
            | Q(user__user__username__icontains=search)
            | Q(user__user__email__icontains=search)
            | Q(user__user__first_name__icontains=search)
            | Q(user__user__last_name__icontains=search)
            | Q(details__setting__icontains=search)
            | Q(details__reason__icontains=search)
        )
    if action:
        queryset = queryset.filter(action__icontains=action)
    if actor:
        queryset = queryset.filter(
            Q(user__user__username__icontains=actor)
            | Q(user__user__email__icontains=actor)
            | Q(user__user__first_name__icontains=actor)
            | Q(user__user__last_name__icontains=actor)
        )
    if object_type:
        queryset = queryset.filter(object_type__icontains=object_type)
    if category == "settings":
        queryset = queryset.filter(
            Q(action__icontains="settings") | Q(object_type__icontains="settings")
        )
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    return queryset


def audit_log_response(request, queryset=None, extra=None):
    if queryset is None:
        queryset = AuditLog.objects.all()
    queryset = filter_audit_logs(
        queryset.select_related("user__user").order_by("-created_at", "-id"),
        request.query_params,
    )
    paginator = AuditLogPagination()
    page = paginator.paginate_queryset(queryset, request)
    response = paginator.get_paginated_response([serialize_audit_log(log) for log in page])
    if extra:
        response.data.update(extra)
    return response


def _changed_fields(request):
    content_type = request.META.get("CONTENT_TYPE", "")
    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        content_length = 0
    if "application/json" not in content_type or content_length > 1_000_000:
        return []
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return []
    return sorted(payload.keys()) if isinstance(payload, dict) else []


def _safe_query_params(request):
    safe_params = {}
    for key, values in request.GET.lists():
        if any(part in key.lower() for part in SENSITIVE_FIELD_PARTS):
            safe_params[key] = ["[redacted]"]
        else:
            safe_params[key] = values
    return safe_params


def _redact_sensitive_values(value, key=""):
    if any(part in key.lower() for part in SENSITIVE_FIELD_PARTS):
        return "[redacted]"
    if isinstance(value, dict):
        return {
            nested_key: _redact_sensitive_values(nested_value, nested_key)
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    return value


def _view_audit_details(request):
    supplied = getattr(request, "audit_details", None)
    if not isinstance(supplied, dict):
        return {}
    return {
        key: _redact_sensitive_values(value, key)
        for key, value in supplied.items()
        if key in VIEW_AUDIT_DETAIL_FIELDS
    }


def set_audit_details(request, details):
    target = getattr(request, "_request", request)
    target.audit_details = details


def _resource_context(request, prefix):
    raw_parts = [part for part in request.path.strip("/").split("/") if part]
    parts = raw_parts[1:] if raw_parts and raw_parts[0] == prefix else raw_parts
    object_id = ""
    descriptive_parts = []

    for part in parts:
        if re.fullmatch(r"\d+", part):
            object_id = object_id or part
        else:
            descriptive_parts.append(part.replace("-", " "))

    if not object_id:
        for key, value in request.GET.items():
            if key == "id" or key.endswith("_id"):
                object_id = value
                break

    resource = " ".join(descriptive_parts).strip() or prefix
    return resource, resource.title(), object_id


def _response_object_id(response):
    data = getattr(response, "data", None)
    if not isinstance(data, dict):
        return ""

    candidate_keys = ("id", "object_id", "profile_id", "programme_id", "course_id")
    for key in candidate_keys:
        if data.get(key) is not None:
            return str(data[key])
    for value in data.values():
        if isinstance(value, dict):
            for key in candidate_keys:
                if value.get(key) is not None:
                    return str(value[key])
    return ""


def _executive_scope_details(profile):
    from executive_app.course_schedule import get_executive_scope, scope_payload

    try:
        scope = get_executive_scope(profile)
    except ValueError:
        return None
    if not scope.get("kind") or not scope.get("unit"):
        return None
    payload = scope_payload(scope)
    return {
        "kind": payload["kind"],
        "id": payload["id"],
        "code": payload["code"],
        "name": payload["name"],
    }


class AuditActionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        changed_fields = _changed_fields(request)
        response = self.get_response(request)

        prefix = request.path.strip("/").split("/", 1)[0]
        expected_role = AUDITED_PREFIXES.get(prefix)
        if (
            request.method not in MUTATING_METHODS
            or not expected_role
            or not 200 <= response.status_code < 300
        ):
            return response

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return response
        profile = Profile.objects.filter(user=user, is_active=True).first()
        if not profile or profile.role != expected_role:
            return response

        resource, object_type, object_id = _resource_context(request, prefix)
        object_id = object_id or _response_object_id(response)
        details = {
            "actor_role": profile.role,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "changed_fields": changed_fields,
            "query_params": _safe_query_params(request),
        }
        details.update(_view_audit_details(request))
        if profile.role == Profile.ROLE_EXECUTIVE:
            scope = _executive_scope_details(profile)
            if scope:
                details["scope"] = scope

        try:
            AuditLog.objects.create(
                user=profile,
                action=f"{MUTATING_METHODS[request.method]} {resource}",
                object_type=object_type,
                object_id=object_id,
                details=details,
            )
        except Exception:
            logger.exception("Unable to record audit action for %s", request.path)

        return response
