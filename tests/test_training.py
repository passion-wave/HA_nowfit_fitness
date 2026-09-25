from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.nowfit.models import Coverage
from custom_components.nowfit.parsers.history import RawVisit
from custom_components.nowfit.training import derive_history, normalize_visits

UTC = ZoneInfo("UTC")
BERLIN = ZoneInfo("Europe/Berlin")


def row(day: int, hour: int, duration: int, activity: str = "Checkin") -> RawVisit:
    start = datetime(2026, 9, day, hour, tzinfo=BERLIN)
    return RawVisit("Now Fit Poing", activity, start, start + timedelta(minutes=duration), duration)


def test_cleanup_and_derived_values() -> None:
    rows = (
        row(25, 8, 72),
        row(24, 8, 90),
        row(23, 8, 80),
        row(22, 8, 75),
        row(21, 8, 60),
        row(20, 8, 100),
        row(19, 8, 93),
        row(25, 8, 0),
        row(24, 8, 90),
    )
    fetched = datetime(2026, 9, 25, 18, tzinfo=UTC)
    snapshot = normalize_visits(rows, fetched, coverage=Coverage.CONFIRMED)
    assert len(snapshot.visits) == 7
    assert snapshot.collapsed_duplicate_count == 2
    assert sum(visit.duration_minutes or 0 for visit in snapshot.visits) == 570
    derived = derive_history(snapshot, fetched, BERLIN)
    assert derived.last_visit.duration_minutes == 72
    assert derived.trainings_this_week == 5
    assert derived.trainings_this_month == 7
    assert derived.trained_today is True
    assert derived.trained_yesterday is True


def test_unknown_coverage_never_turns_missing_day_into_false() -> None:
    now = datetime(2026, 9, 25, 18, tzinfo=UTC)
    snapshot = normalize_visits((row(23, 8, 80),), now, coverage=Coverage.UNKNOWN)
    derived = derive_history(snapshot, now, BERLIN)
    assert derived.trained_today is None
    assert derived.trained_yesterday is None


def test_confirmed_coverage_allows_negative_assertion() -> None:
    now = datetime(2026, 9, 25, 18, tzinfo=UTC)
    snapshot = normalize_visits((row(23, 8, 80),), now, coverage=Coverage.CONFIRMED)
    derived = derive_history(snapshot, now, BERLIN)
    assert derived.trained_today is False
    assert derived.trained_yesterday is False


def test_invalid_and_open_rows_are_flagged_or_rejected() -> None:
    now = datetime(2026, 9, 25, 18, tzinfo=UTC)
    future = RawVisit("Now Fit Poing", "Checkin", now + timedelta(hours=1), None, None)
    wrong_activity = row(24, 8, 30, activity="Sauna")
    open_visit = RawVisit("Now Fit Poing", "Checkin", now - timedelta(hours=1), None, None)
    snapshot = normalize_visits((future, wrong_activity, open_visit), now)
    assert snapshot.rejected_row_count == 2
    assert snapshot.visits[0].completed is False
    assert "open_candidate" in snapshot.visits[0].quality_flags
