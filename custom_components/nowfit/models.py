"""Typed domain models for NowFit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Coverage(StrEnum):
    """Known coverage of a supplied history snapshot."""

    UNKNOWN = "unknown"
    PARTIAL = "partial"
    CONFIRMED = "confirmed"


class SourceStatus(StrEnum):
    """Status of one independently refreshed source."""

    READY = "ready"
    TEMPORARY_ERROR = "temporary_error"
    RATE_LIMITED = "rate_limited"
    AUTH_REQUIRED = "auth_required"
    PARSE_ERROR = "parse_error"


@dataclass(frozen=True, slots=True)
class ClubOccupancy:
    club_id: str
    name: str
    checked_in: int


@dataclass(frozen=True, slots=True)
class OccupancySnapshot:
    clubs: tuple[ClubOccupancy, ...]
    fetched_at: datetime
    status: SourceStatus = SourceStatus.READY

    def club(self, club_id: str) -> ClubOccupancy | None:
        return next((club for club in self.clubs if club.club_id == club_id), None)


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    fetched_at: datetime
    checkins_week: int | None
    checkins_month: int | None
    average_visit_minutes: int | None
    week_goal_current: int | None
    week_goal_target: int | None
    month_goal_current: int | None
    month_goal_target: int | None
    identity_hint: str | None = None


@dataclass(frozen=True, slots=True)
class TrainingVisit:
    record_key: str
    studio: str
    activity: str
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: int | None
    completed: bool
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HistorySnapshot:
    visits: tuple[TrainingVisit, ...]
    fetched_at: datetime
    raw_row_count: int
    collapsed_duplicate_count: int
    rejected_row_count: int
    coverage: Coverage = Coverage.UNKNOWN
    complete_from: datetime | None = None
    complete_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class LoginForm:
    action: str
    method: str
    enctype: str
    email_name: str
    password_name: str
    remember_name: str | None
    hidden_fields: tuple[tuple[str, str], ...]


@dataclass(slots=True)
class NowFitRuntimeData:
    entry_type: str
    occupancy_coordinator: Any | None = None
    account_coordinator: Any | None = None
    history_coordinator: Any | None = None
    auth_manager: Any | None = None
    remove_midnight_listener: Any | None = None
    extra: dict[str, Any] = field(default_factory=dict)
