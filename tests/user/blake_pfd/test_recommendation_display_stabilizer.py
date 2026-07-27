from types import SimpleNamespace

import pytest

from pyefis.user.blake_pfd.core.recommendation_display_stabilizer import (
    RecommendationDisplayStabilizer,
)


def recommendation(
    severity: str,
    title: str,
):
    return SimpleNamespace(
        severity=severity,
        title=title,
        urgency_s=None,
        confidence=None,
    )


def test_caution_activates_after_elapsed_delay() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=1.5,
        clear_delay_s=2.5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    assert stabilizer.update(
        caution,
        timestamp_s=10.0,
    ) is None

    assert stabilizer.update(
        caution,
        timestamp_s=11.4,
    ) is None

    assert stabilizer.update(
        caution,
        timestamp_s=11.5,
    ) is caution


def test_fast_render_cycles_do_not_activate_early() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=1.5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    for timestamp_s in (
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
    ):
        assert stabilizer.update(
            caution,
            timestamp_s=timestamp_s,
        ) is None


def test_warning_displays_immediately() -> None:
    stabilizer = RecommendationDisplayStabilizer()

    warning = recommendation(
        "WARNING",
        "Engine Warning",
    )

    assert stabilizer.update(
        warning,
        timestamp_s=0.0,
    ) is warning


def test_critical_displays_immediately() -> None:
    stabilizer = RecommendationDisplayStabilizer()

    critical = recommendation(
        "CRITICAL",
        "Oil Pressure Advisor",
    )

    assert stabilizer.update(
        critical,
        timestamp_s=0.0,
    ) is critical


def test_active_caution_clears_after_elapsed_delay() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=0.0,
        clear_delay_s=2.5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    normal = recommendation(
        "NORMAL",
        "Normal",
    )

    assert stabilizer.update(
        caution,
        timestamp_s=0.0,
    ) is caution

    assert stabilizer.update(
        normal,
        timestamp_s=1.0,
    ) is caution

    assert stabilizer.update(
        normal,
        timestamp_s=3.4,
    ) is caution

    assert stabilizer.update(
        normal,
        timestamp_s=3.5,
    ) is None


def test_new_caution_replaces_old_after_delay() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=1.5,
        clear_delay_s=2.5,
    )

    cht = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    oil = recommendation(
        "CAUTION",
        "Oil Temperature Advisor",
    )

    stabilizer.update(
        cht,
        timestamp_s=0.0,
    )

    assert stabilizer.update(
        cht,
        timestamp_s=1.5,
    ) is cht

    assert stabilizer.update(
        oil,
        timestamp_s=2.0,
    ) is cht

    assert stabilizer.update(
        oil,
        timestamp_s=3.4,
    ) is cht

    assert stabilizer.update(
        oil,
        timestamp_s=3.5,
    ) is oil


def test_warning_clears_stale_caution_state() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=0.0,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    warning = recommendation(
        "WARNING",
        "Engine Warning",
    )

    normal = recommendation(
        "NORMAL",
        "Normal",
    )

    assert stabilizer.update(
        caution,
        timestamp_s=0.0,
    ) is caution

    assert stabilizer.update(
        warning,
        timestamp_s=1.0,
    ) is warning

    assert stabilizer.update(
        normal,
        timestamp_s=2.0,
    ) is None


def test_updated_active_caution_uses_latest_object() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=0.0,
    )

    first = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    updated = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    updated.urgency_s = 12.0

    assert stabilizer.update(
        first,
        timestamp_s=0.0,
    ) is first

    assert stabilizer.update(
        updated,
        timestamp_s=0.5,
    ) is updated

    assert (
        stabilizer.update(
            updated,
            timestamp_s=0.6,
        ).urgency_s
        == 12.0
    )


def test_invalid_delays_raise_errors() -> None:
    with pytest.raises(
        ValueError,
        match="activate_delay_s",
    ):
        RecommendationDisplayStabilizer(
            activate_delay_s=-1.0,
        )

    with pytest.raises(
        ValueError,
        match="clear_delay_s",
    ):
        RecommendationDisplayStabilizer(
            clear_delay_s=-1.0,
        )
        
def test_status_reports_idle_state() -> None:
    stabilizer = RecommendationDisplayStabilizer()

    status = stabilizer.status(
        timestamp_s=0.0,
    )

    assert status.state == "IDLE"
    assert status.active_title is None
    assert status.pending_title is None
    assert status.seconds_remaining is None


def test_status_reports_pending_countdown() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=1.5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    stabilizer.update(
        caution,
        timestamp_s=10.0,
    )

    status = stabilizer.status(
        timestamp_s=10.6,
    )

    assert status.state == "PENDING"
    assert status.pending_title == "CHT Cooling Advisor"
    assert status.active_title is None
    assert status.seconds_remaining == pytest.approx(
        0.9,
    )


def test_status_reports_active_caution() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=0.0,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    stabilizer.update(
        caution,
        timestamp_s=0.0,
    )

    status = stabilizer.status(
        timestamp_s=1.0,
    )

    assert status.state == "ACTIVE"
    assert status.active_title == "CHT Cooling Advisor"
    assert status.pending_title is None
    assert status.seconds_remaining is None


def test_status_reports_clear_countdown() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=0.0,
        clear_delay_s=2.5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    normal = recommendation(
        "NORMAL",
        "Normal",
    )

    stabilizer.update(
        caution,
        timestamp_s=0.0,
    )

    stabilizer.update(
        normal,
        timestamp_s=1.0,
    )

    status = stabilizer.status(
        timestamp_s=2.0,
    )

    assert status.state == "CLEARING"
    assert status.active_title == "CHT Cooling Advisor"
    assert status.seconds_remaining == pytest.approx(
        1.5,
    )


def test_status_reports_replacement_pending_with_active_title() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=1.5,
    )

    cht = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    oil = recommendation(
        "CAUTION",
        "Oil Temperature Advisor",
    )

    stabilizer.update(
        cht,
        timestamp_s=0.0,
    )

    stabilizer.update(
        cht,
        timestamp_s=1.5,
    )

    stabilizer.update(
        oil,
        timestamp_s=2.0,
    )

    status = stabilizer.status(
        timestamp_s=2.5,
    )

    assert status.state == "PENDING"
    assert status.active_title == "CHT Cooling Advisor"
    assert status.pending_title == "Oil Temperature Advisor"
    assert status.seconds_remaining == pytest.approx(
        1.0,
    )
    
def test_nan_timestamp_raises_error() -> None:
    stabilizer = RecommendationDisplayStabilizer()

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    with pytest.raises(
        ValueError,
        match="timestamp_s must be finite",
    ):
        stabilizer.update(
            caution,
            timestamp_s=float("nan"),
        )


def test_infinite_timestamp_raises_error() -> None:
    stabilizer = RecommendationDisplayStabilizer()

    with pytest.raises(
        ValueError,
        match="timestamp_s must be finite",
    ):
        stabilizer.status(
            timestamp_s=float("inf"),
        )


def test_infinite_delay_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="activate_delay_s",
    ):
        RecommendationDisplayStabilizer(
            activate_delay_s=float("inf"),
        )

    with pytest.raises(
        ValueError,
        match="clear_delay_s",
    ):
        RecommendationDisplayStabilizer(
            clear_delay_s=float("nan"),
        )


def test_backwards_timestamp_does_not_activate_caution() -> None:
    stabilizer = RecommendationDisplayStabilizer(
        activate_delay_s=1.5,
    )

    caution = recommendation(
        "CAUTION",
        "CHT Cooling Advisor",
    )

    assert stabilizer.update(
        caution,
        timestamp_s=10.0,
    ) is None

    assert stabilizer.update(
        caution,
        timestamp_s=9.0,
    ) is None

    assert stabilizer.update(
        caution,
        timestamp_s=11.5,
    ) is caution