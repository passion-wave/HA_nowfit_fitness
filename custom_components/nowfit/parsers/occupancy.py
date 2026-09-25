"""Parse the public club occupancy page."""

from __future__ import annotations

from bs4 import Tag

from ..exceptions import AmbiguousClub, ParseError
from ..models import ClubOccupancy
from .common import integer, soup, text


def _card_for_heading(heading: Tag) -> Tag | None:
    node: Tag | None = heading
    while node is not None:
        if node.name == "div" and node.get("id") and node.find("label"):
            return node
        parent = node.parent
        node = parent if isinstance(parent, Tag) else None
    return None


def parse_occupancy(html: str) -> tuple[ClubOccupancy, ...]:
    """Return all unambiguous clubs from one public response."""
    document = soup(html)
    clubs: list[ClubOccupancy] = []
    seen: set[str] = set()
    for heading in document.find_all(["h3", "h4", "h5"]):
        name = text(heading.get_text(" ", strip=True))
        if not name.casefold().startswith("now fit "):
            continue
        card = _card_for_heading(heading)
        if card is None:
            continue
        club_id = str(card.get("id", "")).strip()
        if not club_id:
            raise ParseError("missing_club_id")
        labels = card.find_all("label")
        matches: list[int] = []
        for index, label in enumerate(labels[:-1]):
            label_text = text(label.get_text(" ", strip=True)).rstrip(":").casefold()
            if label_text != "aktuell eingecheckt":
                continue
            matches.append(integer(labels[index + 1].get_text(" ", strip=True), "checked_in"))
        if len(matches) != 1:
            raise ParseError(f"ambiguous_occupancy:{club_id}")
        if club_id in seen or any(item.name.casefold() == name.casefold() for item in clubs):
            raise AmbiguousClub(name)
        seen.add(club_id)
        clubs.append(ClubOccupancy(club_id=club_id, name=name, checked_in=matches[0]))
    if not clubs:
        raise ParseError("no_clubs")
    return tuple(clubs)
