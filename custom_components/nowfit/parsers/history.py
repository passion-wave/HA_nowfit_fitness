"""Parse the member training-times table."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from ..exceptions import ParseError
from .common import soup, text

_DURATION = re.compile(r"(?:(?P<hours>[0-9]+)\s*Std)?\s*(?:(?P<minutes>[0-9]+)\s*Min)?", re.I)
_DATE_FORMAT = "%d.%m.%Y %H:%M"


@dataclass(frozen=True, slots=True)
class RawVisit:
    studio: str
    activity: str
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: int | None


def _local_datetime(value: str, timezone: ZoneInfo) -> datetime:
    naive = datetime.strptime(text(value), _DATE_FORMAT)
    candidate = naive.replace(tzinfo=timezone)
    roundtrip = candidate.astimezone(ZoneInfo("UTC")).astimezone(timezone).replace(tzinfo=None)
    if roundtrip != naive:
        raise ParseError("nonexistent_local_time")
    if candidate.replace(fold=0).utcoffset() != candidate.replace(fold=1).utcoffset():
        raise ParseError("ambiguous_local_time")
    return candidate


def _duration(value: str) -> int | None:
    normalized = text(value)
    if not normalized:
        return None
    match = _DURATION.fullmatch(normalized)
    if match is None or not any(match.groupdict().values()):
        raise ParseError("invalid_duration")
    return int(match.group("hours") or 0) * 60 + int(match.group("minutes") or 0)


def parse_history(html: str, timezone: ZoneInfo) -> tuple[RawVisit, ...]:
    document = soup(html)
    if document.find("input", attrs={"type": "password"}) is not None:
        raise ParseError("login_page")
    visits: list[RawVisit] = []
    for row in document.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        mapped: dict[str, str] = {}
        for cell in cells:
            title = cell.get("data-title")
            if title:
                mapped[text(str(title)).casefold()] = text(cell.get_text(" ", strip=True))
        if not mapped or "datum von" not in mapped:
            continue
        try:
            visits.append(
                RawVisit(
                    studio=mapped["studio"],
                    activity=mapped["leistung"],
                    started_at=_local_datetime(mapped["datum von"], timezone),
                    ended_at=_local_datetime(mapped["datum bis"], timezone)
                    if mapped.get("datum bis")
                    else None,
                    duration_minutes=_duration(mapped.get("dauer", "")),
                )
            )
        except (KeyError, ValueError) as err:
            raise ParseError("invalid_history_row") from err
    if not visits and document.find("table") is None:
        raise ParseError("history_table_missing")
    return tuple(visits)
