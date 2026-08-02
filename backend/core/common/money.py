"""Shared money/decimal helpers.

``format_money`` mirrors the common "format a Decimal as a 2dp string, fall back
to a default on bad input" pattern. ``parse_decimal`` is a validating parser for
endpoints that must reject invalid/negative amounts.

Note: some callers use app-specific formatting (e.g. ``str(value)`` or
``.quantize(...)`` with a particular rounding contract). Only migrate a caller to
these helpers when the output/validation behaviour is genuinely identical.
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

MONEY_QUANT = Decimal("0.01")


def format_money(value, default="0.00"):
    """Format ``value`` as a 2-decimal string, returning ``default`` on failure."""
    try:
        return f"{Decimal(value):.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return default


def parse_decimal(value, field="amount", *, allow_zero=False, allow_negative=False):
    """Parse ``value`` into a ``Decimal`` or raise DRF-friendly ``ValidationError``.

    - ``allow_negative=False`` (default) rejects amounts ``< 0``.
    - ``allow_zero=False`` (default) rejects amounts ``<= 0``.
    Set both to widen the accepted range.
    """
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({field: "Enter a valid amount."}) from exc
    if not allow_negative and amount < 0:
        raise ValidationError({field: "Amount cannot be negative."})
    if not allow_zero and amount <= 0:
        raise ValidationError({field: "Amount must be greater than zero."})
    return amount
