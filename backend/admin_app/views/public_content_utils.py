from django.utils import timezone
from django.utils.text import slugify

from core.common.errors import first_error


def request_payload(request):
    return request.data.copy()


def profile_for_request(request):
    return getattr(request.user, "profile", None)


def normalize_slug(payload, max_length=140):
    slug = str(payload.get("slug", "") or "").strip()
    if slug:
        payload["slug"] = slugify(slug)[:max_length]
        return payload

    title = str(payload.get("title", "") or "").strip()
    if title:
        payload["slug"] = slugify(title)[:max_length]
    return payload


def normalize_route_path(payload):
    route_path = str(payload.get("route_path", "") or "").strip()
    if route_path:
        payload["route_path"] = (
            "/" if route_path == "/" else f"/{route_path.strip('/')}"
        )
    return payload


def save_serializer(serializer, success_message, status_code, **save_kwargs):
    if not serializer.is_valid():
        return None, {
            "detail": first_error(serializer.errors),
            "errors": serializer.errors,
        }, 400

    instance = serializer.save(**save_kwargs)
    return instance, {"message": success_message}, status_code


def publish_now_if_needed(payload, status_value="published"):
    if payload.get("status") == status_value and not payload.get("published_at"):
        payload["published_at"] = timezone.now()
    return payload
