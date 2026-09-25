"""Pure helpers for config-flow presentation data."""

from __future__ import annotations

import re

from .models import ClubOccupancy

_SAFE_ERROR_CODE = re.compile(r"^[a-z0-9_:.-]{1,80}$")


def club_selector_options(clubs: tuple[ClubOccupancy, ...]) -> list[dict[str, str]]:
    """Return the list shape required by Home Assistant's select selector."""
    return [{"value": club.club_id, "label": club.name} for club in clubs]


def safe_error_code(error: Exception) -> str:
    """Return only allowlisted internal codes, never response or credential data."""
    value = str(error)
    return value if _SAFE_ERROR_CODE.fullmatch(value) else "redacted"
