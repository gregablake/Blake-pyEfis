from pyefis.user.blake_pfd.core.recommendation_display_stabilizer import (
    RecommendationDisplayStatus,
    format_recommendation_display_status,
)


def test_idle_status_formats_as_empty_text() -> None:
    status = RecommendationDisplayStatus()

    assert format_recommendation_display_status(
        status
    ) == ""


def test_pending_status_includes_title_and_countdown() -> None:
    status = RecommendationDisplayStatus(
        state="PENDING",
        pending_title="CHT Cooling Advisor",
        seconds_remaining=0.9,
    )

    assert format_recommendation_display_status(
        status
    ) == "CHT Cooling Advisor pending 0.9s"


def test_active_status_displays_active_title() -> None:
    status = RecommendationDisplayStatus(
        state="ACTIVE",
        active_title="Oil Temperature Advisor",
    )

    assert format_recommendation_display_status(
        status
    ) == "Oil Temperature Advisor"


def test_clearing_status_includes_countdown() -> None:
    status = RecommendationDisplayStatus(
        state="CLEARING",
        active_title="CHT Cooling Advisor",
        seconds_remaining=1.5,
    )

    assert format_recommendation_display_status(
        status
    ) == "CHT Cooling Advisor clearing 1.5s"


def test_pending_status_handles_missing_title() -> None:
    status = RecommendationDisplayStatus(
        state="PENDING",
        seconds_remaining=1.0,
    )

    assert format_recommendation_display_status(
        status
    ) == "Caution pending 1.0s"


def test_active_status_handles_missing_title() -> None:
    status = RecommendationDisplayStatus(
        state="ACTIVE",
    )

    assert format_recommendation_display_status(
        status
    ) == "Caution active"