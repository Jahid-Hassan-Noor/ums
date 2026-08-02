"""Shared pagination helper used across list/service endpoints.

Many services repeated the same offset-slice + metadata math. ``paginate``
centralizes that logic and works with either a Django ``QuerySet`` (uses
``.count()`` for an efficient total) or a plain in-memory ``list``.
"""


def pagination_meta(total, page, page_size):
    """Return the standard ``{total, page, page_size, total_pages}`` metadata."""
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def paginate(items, page=1, page_size=20):
    """Slice ``items`` for ``page``/``page_size`` and return ``(page_items, meta)``.

    ``items`` may be a Django ``QuerySet`` (``.count()`` is used for the total)
    or any sliceable sequence (``len()`` is used). Callers build their final
    payload dict, e.g. ``{"entries": page_items, **meta}``.
    """
    count = getattr(items, "count", None)
    total = count() if callable(count) else len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], pagination_meta(total, page, page_size)
