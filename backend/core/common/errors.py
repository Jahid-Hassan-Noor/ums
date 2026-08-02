"""Shared error/response helpers used across all apps.

These were previously copy-pasted into many view/service modules (often named
``first_error`` or ``_first_error``). Consolidating them here removes dozens of
identical definitions and a single source of truth for serializer error text.
"""

from rest_framework.response import Response

DEFAULT_ERROR_MESSAGE = "Operation failed."


def first_error(errors, default=DEFAULT_ERROR_MESSAGE):
    """Flatten DRF ``serializer.errors`` into a single ``"field: message"`` string.

    Accepts nested dicts and lists. Returns ``default`` when nothing useful is
    found (callers may pass a context-specific fallback, e.g. account creation).
    """
    if isinstance(errors, dict):
        for field, value in errors.items():
            if isinstance(value, list) and value:
                return f"{field}: {value[0]}"
            if isinstance(value, dict):
                nested = first_error(value, default=default)
                if nested:
                    return nested
            if value:
                return f"{field}: {value}"
    if isinstance(errors, list) and errors:
        return str(errors[0])
    return default


def validation_error_response(errors, default=DEFAULT_ERROR_MESSAGE, status_code=400):
    """Build a standard ``{"detail": ..., "errors": ...}`` error Response."""
    return Response(
        {"detail": first_error(errors, default=default), "errors": errors},
        status=status_code,
    )
