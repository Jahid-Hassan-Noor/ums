"""Shared backend utilities.

This package centralizes small helpers that were previously copy-pasted across
many apps (serializer error formatting, profile loading/display, money math,
pagination, request parsing, etc.). Import from here instead of re-defining.

Modules:
    errors.py         - ``first_error``, ``validation_error_response``
    profiles.py       - ``profile_display_name``, ``profile_identifier``,
                        ``get_role_profile`` and role helpers
    money.py          - ``format_money``, ``parse_decimal``
    pagination.py     - ``paginate``, ``pagination_meta``
    request_utils.py  - ``parse_bool``, ``parse_int``, ``parse_json``
"""
