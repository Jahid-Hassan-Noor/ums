"""Shared request/param parsing helpers used across views and services.

These small coercion helpers were previously copy-pasted into several view
modules. Consolidating them keeps parsing behaviour consistent everywhere.
"""

import json


def parse_bool(value, default=False):
    """Coerce a request value into a bool.

    Empty/``None`` returns ``default``. Truthy string tokens are
    ``{"1", "true", "yes", "on"}`` (case-insensitive).
    """
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_int(value, default=0):
    """Coerce a value into an int, returning ``default`` on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_json(value, default):
    """Coerce a value into parsed JSON, returning ``default`` on failure.

    Values that are already ``list``/``dict`` are returned unchanged.
    """
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
