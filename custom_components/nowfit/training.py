"""Visit cleanup and local date derivations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from zoneinfo import ZoneInfo

from .models import Coverage, HistorySnapshot, TrainingVisit
from .parsers.history import RawVisit


def _key(raw: RawVisit) -> str:
    material = "\x1f".join(
        (
            raw.studio.strip().casefold(),
            raw.activity.strip().casefold(),
            raw.started_at.astimezone(ZoneInfo("UTC")).isoformat(),
        )
    )
    return sha256(material.encode()).hexdigest()[:24]


def normalize_visits(
    raw_visits: tuple[RawVisit, ...],
    fetched_at: datetime,
    minimum_duration: int = 1,
    coverage: Coverage = Coverage.UNKNOWN,
) -> HistorySnapshot:
    """Normalize, collapse paired zero rows, reject unsafe intervals and sort."""
    exact_seen: set[RawVisit] = set()
    groups: dict[tuple[str, str, datetime], list[RawVisit]] = defaultdict(list)
    rejected = 0
    collapsed = 0
    for raw in raw_visits:
        if raw in exact_seen:
            collapsed += 1
            continue
        exact_seen.add(raw)
        groups[(raw.studio.casefold(), raw.activity.casefold(), raw.started_at)].append(raw)

    selected: list[RawVisit] = []
    for rows in groups.values():
        positive = [row for row in rows if (row.duration_minutes or 0) > 0]
        zero = [row for row in rows if row.duration_minutes == 0]
        if len(positive) == 1 and zero:
            selected.append(positive[0])
            collapsed += len(zero)
        else:
            selected.extend(rows)

    visits: list[TrainingVisit] = []
    now_utc = fetched_at.astimezone(ZoneInfo("UTC"))
    for raw in selected:
        flags: list[str] = []
        start_utc = raw.started_at.astimezone(ZoneInfo("UTC"))
        end_utc = raw.ended_at.astimezone(ZoneInfo("UTC")) if raw.ended_at else None
        if raw.activity.casefold() != "checkin":
            rejected += 1
            continue
        if start_utc > now_utc or (end_utc is not None and end_utc < start_utc):
            rejected += 1
            continue
        computed = int((end_utc - start_utc).total_seconds() // 60) if end_utc else None
        if raw.duration_minutes is not None and computed is not None:
            if abs(raw.duration_minutes - computed) > 1:
                flags.append("duration_mismatch")
        completed = end_utc is not None and (raw.duration_minutes or 0) >= minimum_duration
        if not completed:
            if raw.duration_minutes == 0:
                flags.append("zero_duration")
            if end_utc is None:
                flags.append("open_candidate")
        visits.append(
            TrainingVisit(
                record_key=_key(raw),
                studio=raw.studio,
                activity=raw.activity,
                started_at=start_utc,
                ended_at=end_utc,
                duration_minutes=raw.duration_minutes,
                completed=completed,
                quality_flags=tuple(flags),
            )
        )
    visits.sort(key=lambda visit: visit.started_at, reverse=True)
    return HistorySnapshot(
        visits=tuple(visits),
        fetched_at=fetched_at,
        raw_row_count=len(raw_visits),
        collapsed_duplicate_count=collapsed,
        rejected_row_count=rejected,
        coverage=coverage,
    )


@dataclass(frozen=True, slots=True)
class HistoryDerived:
    last_visit: TrainingVisit | None
    trainings_this_week: int
    trainings_this_month: int
    days_since_last_training: int | None
    trained_today: bool | None
    trained_yesterday: bool | None


def derive_history(snapshot: HistorySnapshot, now: datetime, timezone: ZoneInfo) -> HistoryDerived:
    local_now = now.astimezone(timezone)
    today = local_now.date()
    yesterday = date.fromordinal(today.toordinal() - 1)
    iso_year, iso_week, _ = today.isocalendar()
    completed = [visit for visit in snapshot.visits if visit.completed]
    local_dates = [(visit, visit.started_at.astimezone(timezone).date()) for visit in completed]
    last = completed[0] if completed else None
    found_today = any(day == today for _, day in local_dates)
    found_yesterday = any(day == yesterday for _, day in local_dates)
    negatives_are_known = snapshot.coverage is Coverage.CONFIRMED
    return HistoryDerived(
        last_visit=last,
        trainings_this_week=sum(
            1 for _, day in local_dates if day.isocalendar()[:2] == (iso_year, iso_week)
        ),
        trainings_this_month=sum(
            1 for _, day in local_dates if (day.year, day.month) == (today.year, today.month)
        ),
        days_since_last_training=(today - last.started_at.astimezone(timezone).date()).days
        if last
        else None,
        trained_today=True if found_today else (False if negatives_are_known else None),
        trained_yesterday=True if found_yesterday else (False if negatives_are_known else None),
    )
