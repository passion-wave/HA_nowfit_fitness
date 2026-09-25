from custom_components.nowfit.dashboard import personal_dashboard, public_dashboard


def ids() -> dict[str, str]:
    keys = (
        "occupancy",
        "public_last_success",
        "public_refresh",
        "week_goal_current",
        "week_goal_display_percent",
        "checkins_month",
        "last_training_start",
        "last_training_duration",
        "trained_today",
        "trained_yesterday",
        "member_refresh",
    )
    return {key: f"sensor.test_{key}" for key in keys}


def test_public_dashboard_uses_resolved_ids() -> None:
    dashboard = public_dashboard(ids())
    assert dashboard["views"][0]["type"] == "sections"
    assert "sensor.test_occupancy" in str(dashboard)


def test_personal_dashboard_has_three_mobile_ordered_sections() -> None:
    dashboard = personal_dashboard(ids())
    sections = dashboard["views"][0]["sections"]
    assert len(sections) == 3
    assert [section["cards"][0]["heading"] for section in sections] == [
        "Jetzt im Studio",
        "Meine Ziele",
        "Mein Verlauf",
    ]
