from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from custom_components.nowfit.exceptions import AmbiguousClub, ParseError, UnsafeRedirect
from custom_components.nowfit.parsers.account import parse_account
from custom_components.nowfit.parsers.history import parse_history
from custom_components.nowfit.parsers.login import parse_login_form
from custom_components.nowfit.parsers.occupancy import parse_occupancy

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_occupancy_accepts_real_zero() -> None:
    clubs = parse_occupancy(fixture("occupancy.html"))
    assert [(club.club_id, club.checked_in) for club in clubs] == [
        ("club-poing", 0),
        ("club-grafing", 17),
    ]


@pytest.mark.parametrize(
    "html,error",
    [
        ("<html></html>", ParseError),
        (
            "<div id='x'><h4>Now Fit X</h4>"
            "<label>Aktuell eingecheckt:</label><label>n/a</label></div>",
            ParseError,
        ),
        (
            "<div id='x'><h4>Now Fit X</h4>"
            "<label>Aktuell eingecheckt:</label><label>1</label></div>" * 2,
            AmbiguousClub,
        ),
    ],
)
def test_occupancy_rejects_ambiguous_or_invalid(html, error) -> None:
    with pytest.raises(error):
        parse_occupancy(html)


def test_login_form_is_discovered_and_checkbox_hidden_duplicate_removed() -> None:
    form = parse_login_form(fixture("login.html"))
    assert form.email_name == "Email"
    assert form.password_name == "Password"
    assert form.remember_name == "RememberMe"
    assert form.hidden_fields == (("__RequestVerificationToken", "synthetic-token"),)


def test_login_form_rejects_cross_origin_action() -> None:
    html = fixture("login.html").replace("/Account/Login", "https://example.net/login")
    with pytest.raises(UnsafeRedirect):
        parse_login_form(html)


def test_account_parser() -> None:
    fetched = datetime(2026, 9, 25, tzinfo=ZoneInfo("UTC"))
    account = parse_account(fixture("account.html"), fetched)
    assert (account.checkins_week, account.checkins_month) == (2, 7)
    assert account.average_visit_minutes == 81
    assert (account.week_goal_current, account.week_goal_target) == (2, 3)
    assert (account.month_goal_current, account.month_goal_target) == (7, 12)


def test_history_parser() -> None:
    visits = parse_history(fixture("history.html"), ZoneInfo("Europe/Berlin"))
    assert len(visits) == 2
    assert visits[0].duration_minutes == 72
    assert visits[0].started_at.utcoffset().total_seconds() == 7200


def test_history_rejects_nonexistent_dst_time() -> None:
    html = fixture("history.html").replace("22.09.2026 17:00", "29.03.2026 02:30")
    with pytest.raises(ParseError, match="nonexistent_local_time"):
        parse_history(html, ZoneInfo("Europe/Berlin"))


def test_account_and_history_reject_login_page() -> None:
    html = "<html><form><input type='password' name='Password'></form></html>"
    fetched = datetime(2026, 9, 25, tzinfo=ZoneInfo("UTC"))
    with pytest.raises(ParseError, match="login_page"):
        parse_account(html, fetched)
    with pytest.raises(ParseError, match="login_page"):
        parse_history(html, ZoneInfo("Europe/Berlin"))


def test_empty_history_table_is_valid_but_missing_table_is_not() -> None:
    assert parse_history("<table></table>", ZoneInfo("Europe/Berlin")) == ()
    with pytest.raises(ParseError, match="history_table_missing"):
        parse_history("<html><body>none</body></html>", ZoneInfo("Europe/Berlin"))
