"""Pure helpers for config-flow presentation data."""

from __future__ import annotations

from .models import ClubOccupancy


def club_selector_options(clubs: tuple[ClubOccupancy, ...]) -> list[dict[str, str]]:
    """Return the list shape required by Home Assistant's select selector."""
    return [{"value": club.club_id, "label": club.name} for club in clubs]
