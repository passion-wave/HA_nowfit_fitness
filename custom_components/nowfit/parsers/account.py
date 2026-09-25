"""Parse normalized account counters and goals."""

from __future__ import annotations

import re
from datetime import datetime

from ..exceptions import ParseError
from ..models import AccountSnapshot
from .common import integer, soup, text

_GOAL = re.compile(r"(?P<current>[0-9]+)\s*/\s*(?P<target>[0-9]+)")
_MINUTES = re.compile(r"(?P<minutes>[0-9]+)\s*(?:min|minute)", re.I)


def _value_after_label(document, label: str) -> str | None:
    wanted = label.casefold()
    for node in document.find_all(string=True):
        if wanted not in text(str(node)).casefold():
            continue
        parent = node.parent
        if parent is None:
            continue
        container = parent.parent or parent
        heading = container.find(["h1", "h2", "h3", "strong"])
        if heading is not None:
            return text(heading.get_text(" ", strip=True))
        sibling = parent.find_next(["h1", "h2", "h3", "strong"])
        if sibling is not None:
            return text(sibling.get_text(" ", strip=True))
    return None


def parse_account(html: str, fetched_at: datetime) -> AccountSnapshot:
    document = soup(html)
    if document.find("input", attrs={"type": "password"}) is not None:
        raise ParseError("login_page")
    week = _value_after_label(document, "Checkins akt. Woche")
    month = _value_after_label(document, "Checkins akt. Mon.")
    average = _value_after_label(document, "Durch. Checkin Dauer")
    week_goal = _value_after_label(document, "Checkinziel diese Woche")
    month_goal = _value_after_label(document, "Checkinziel diesen Monat")
    if all(value is None for value in (week, month, average, week_goal, month_goal)):
        raise ParseError("account_markers_missing")
    average_match = _MINUTES.search(average or "")
    week_match = _GOAL.search(week_goal or "")
    month_match = _GOAL.search(month_goal or "")
    return AccountSnapshot(
        fetched_at=fetched_at,
        checkins_week=integer(week, "checkins_week") if week is not None else None,
        checkins_month=integer(month, "checkins_month") if month is not None else None,
        average_visit_minutes=int(average_match.group("minutes")) if average_match else None,
        week_goal_current=int(week_match.group("current")) if week_match else None,
        week_goal_target=int(week_match.group("target")) if week_match else None,
        month_goal_current=int(month_match.group("current")) if month_match else None,
        month_goal_target=int(month_match.group("target")) if month_match else None,
    )
