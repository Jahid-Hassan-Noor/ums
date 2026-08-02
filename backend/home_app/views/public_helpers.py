from django.db.models import Q
from django.utils import timezone

from home_app import models
from home_app.serializers import PublicPageSerializer


def normalize_route_path(route_path):
    value = str(route_path or "/").strip()
    if not value or value == "/":
        return "/"
    return f"/{value.strip('/')}"


def published_filter(field="published_at"):
    now = timezone.now()
    return Q(**{f"{field}__isnull": True}) | Q(**{f"{field}__lte": now})


def published_pages():
    return models.PublicPage.objects.filter(
        status=models.PublicPage.STATUS_PUBLISHED
    ).filter(published_filter())


def get_public_page(route_path=None, slug=None):
    queryset = published_pages()
    if slug:
        return queryset.filter(slug=slug).first()
    return queryset.filter(route_path=normalize_route_path(route_path)).first()


def public_page_payload(request, route_path, fallback_title, section):
    page = get_public_page(route_path=route_path)
    return {
        "title": page.title if page else fallback_title,
        "section": section,
        "page": PublicPageSerializer(page, context={"request": request}).data
        if page
        else None,
    }


def published_news():
    return (
        models.PublicNews.objects.filter(status=models.PublicNews.STATUS_PUBLISHED)
        .filter(published_filter())
        .order_by("-published_at", "-created_at")
    )


def published_events():
    return models.PublicEvent.objects.filter(
        status=models.PublicEvent.STATUS_PUBLISHED
    ).order_by("starts_at")


def public_announcements():
    now = timezone.now()
    return (
        models.PublicAnnouncement.objects.filter(
            is_published=True,
            audience=models.PublicAnnouncement.AUDIENCE_PUBLIC,
        )
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .order_by("-is_pinned", "-starts_at", "-created_at")
    )


def public_official_links():
    return models.OfficialLink.objects.filter(
        is_active=True,
        audience=models.OfficialLink.AUDIENCE_PUBLIC,
    ).order_by("category", "sort_order", "title")
