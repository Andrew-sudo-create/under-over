from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re


_NON_NUMERIC = re.compile(r"[^0-9.,-]+")


def parse_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value

    cleaned = _NON_NUMERIC.sub("", value).replace(",", "")
    if not cleaned:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def parse_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)

    cleaned = _NON_NUMERIC.sub("", value).replace(",", "")
    if cleaned.count(".") > 1:
        # malformed number; keep only first decimal point
        first = cleaned.find(".")
        cleaned = cleaned[: first + 1] + cleaned[first + 1 :].replace(".", "")
    if not cleaned:
        return None

    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        return None


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None
