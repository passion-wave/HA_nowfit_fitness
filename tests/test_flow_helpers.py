from custom_components.nowfit.flow_helpers import club_selector_options
from custom_components.nowfit.models import ClubOccupancy


def test_club_selector_options_use_home_assistant_sequence_shape() -> None:
    clubs = (
        ClubOccupancy("poing", "Now Fit Poing", 12),
        ClubOccupancy("grafing", "Now Fit Grafing", 7),
    )

    assert club_selector_options(clubs) == [
        {"value": "poing", "label": "Now Fit Poing"},
        {"value": "grafing", "label": "Now Fit Grafing"},
    ]
