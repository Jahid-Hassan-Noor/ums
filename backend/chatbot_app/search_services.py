import re
from html import unescape

from django.db import connection
from django.db.models import Q
from django.utils import timezone

from chatbot_app.models import SearchDocument
from chatbot_app.search_permissions import (
    FORBIDDEN_DOCUMENT_TYPES,
    FORBIDDEN_DOMAINS,
    base_visibility_filter,
    has_index_access,
    source_object_is_available,
)

try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
except Exception:  # pragma: no cover - only used when postgres search is unavailable.
    SearchQuery = SearchRank = SearchVector = None


MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 150
MODE_LIMITS = {
    "topbar": 10,
    "chatbot": 5,
    "full": 50,
}
DEFAULT_LIMITS = {
    "topbar": 8,
    "chatbot": 4,
    "full": 10,
}
SEARCH_STOP_WORDS = {
    "about",
    "and",
    "are",
    "can",
    "find",
    "for",
    "from",
    "how",
    "is",
    "me",
    "of",
    "show",
    "tell",
    "the",
    "this",
    "what",
    "where",
}


def normalize_query(query):
    return " ".join(str(query or "").split())[:MAX_QUERY_LENGTH]


def validate_query(query):
    normalized = normalize_query(query)
    if len(normalized) < MIN_QUERY_LENGTH:
        raise ValueError("Search query must be at least 2 characters.")
    return normalized


def _clean_text(value):
    text = unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return " ".join(text.split())


def _fallback_search(queryset, query):
    tokens = [token for token in re.split(r"\W+", query) if len(token) >= 2]
    if not tokens:
        return queryset.none()

    text_filter = Q()
    for token in tokens[:6]:
        token_filter = (
            Q(title__icontains=token)
            | Q(summary__icontains=token)
            | Q(body__icontains=token)
            | Q(keywords__icontains=token)
        )
        text_filter &= token_filter
    return queryset.filter(text_filter).order_by("-last_indexed_at", "title")


def _query_tokens(query):
    return [
        token.lower()
        for token in re.split(r"\W+", query)
        if len(token) >= 3 and token.lower() not in SEARCH_STOP_WORDS
    ]


def _document_contains_query_token(document, query):
    tokens = _query_tokens(query)
    if not tokens:
        return True
    text_tokens = set(re.split(
        r"\W+",
        _clean_text(
            f"{document.title} {document.summary} {document.keywords} {document.body}"
        ).lower(),
    ))
    return any(token in text_tokens for token in tokens)


def _apply_search(queryset, query):
    if connection.vendor == "postgresql" and SearchVector and SearchQuery:
        vector = (
            SearchVector("title", weight="A", config="english")
            + SearchVector("summary", weight="B", config="english")
            + SearchVector("keywords", weight="B", config="english")
            + SearchVector("body", weight="C", config="english")
        )
        search_query = SearchQuery(query, search_type="websearch", config="english")
        return (
            queryset.annotate(search_rank=SearchRank(vector, search_query))
            .filter(search_rank__gt=0)
            .order_by("-search_rank", "-last_indexed_at", "title")
        )
    return _fallback_search(queryset, query)


def _snippet(document, query, max_length=220):
    source = _clean_text(document.summary or document.body or document.title)
    if len(source) <= max_length:
        return source

    lowered = source.lower()
    tokens = [token.lower() for token in re.split(r"\W+", query) if len(token) >= 2]
    first_match = min(
        (lowered.find(token) for token in tokens if lowered.find(token) >= 0),
        default=0,
    )
    start = max(first_match - 55, 0)
    end = min(start + max_length, len(source))
    if end - start < max_length:
        start = max(end - max_length, 0)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(source) else ""
    return f"{prefix}{source[start:end].strip()}{suffix}"


def _safe_metadata(document):
    metadata = document.safe_metadata or {}
    allowed_keys = {
        "category",
        "course_code",
        "course_title",
        "location",
        "semester",
        "section",
    }
    return {key: metadata[key] for key in allowed_keys if key in metadata}


def serialize_search_result(document, query, *, mode):
    result = {
        "title": document.title,
        "summary": _snippet(document, query),
        "domain": document.domain,
        "type": document.document_type,
        "icon": document.icon,
        "url": document.source_url,
        "breadcrumbs": document.breadcrumbs or [],
        "source_label": document.source_label or document.title,
        "metadata": _safe_metadata(document),
    }
    if mode == "chatbot":
        result["last_indexed_at"] = timezone.localtime(document.last_indexed_at).isoformat()
    return result


def _candidate_queryset(user, *, domain=None, document_type=None):
    queryset = SearchDocument.objects.filter(is_active=True)
    queryset = queryset.exclude(domain__in=FORBIDDEN_DOMAINS)
    queryset = queryset.exclude(document_type__in=FORBIDDEN_DOCUMENT_TYPES)
    queryset = queryset.filter(base_visibility_filter(user))
    if domain:
        queryset = queryset.filter(domain=domain)
    if document_type:
        queryset = queryset.filter(document_type=document_type)
    return queryset


def search_documents(
    *,
    user,
    query,
    mode="topbar",
    domain=None,
    document_type=None,
    limit=None,
    page=1,
    page_size=None,
):
    normalized_query = validate_query(query)
    mode = mode if mode in MODE_LIMITS else "topbar"
    max_limit = MODE_LIMITS[mode]
    requested_limit = limit or DEFAULT_LIMITS[mode]
    requested_limit = max(1, min(int(requested_limit), max_limit))
    page = max(1, int(page or 1))
    page_size = max(1, min(int(page_size or requested_limit), max_limit))

    queryset = _candidate_queryset(user, domain=domain, document_type=document_type)
    queryset = _apply_search(queryset, normalized_query)

    # Permission checks can depend on course membership and source availability,
    # so fetch a small overage and filter in Python before slicing the response.
    fetch_limit = max(requested_limit * 8, page * page_size * 4, 40)
    documents = list(queryset[:fetch_limit])
    allowed_documents = []
    for document in documents:
        if not _document_contains_query_token(document, normalized_query):
            continue
        if not has_index_access(user, document):
            continue
        if not source_object_is_available(document):
            continue
        allowed_documents.append(document)

    if mode == "full":
        start = (page - 1) * page_size
        end = start + page_size
        selected_documents = allowed_documents[start:end]
    else:
        selected_documents = allowed_documents[:requested_limit]

    results = [
        serialize_search_result(document, normalized_query, mode=mode)
        for document in selected_documents
    ]
    return {
        "query": normalized_query,
        "mode": mode,
        "count": len(allowed_documents),
        "results": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "has_next": mode == "full" and len(allowed_documents) > page * page_size,
        },
    }


def retrieve_for_chatbot(user, question, *, limit=4, domain=None, document_type=None):
    return search_documents(
        user=user,
        query=question,
        mode="chatbot",
        domain=domain,
        document_type=document_type,
        limit=limit,
    )
