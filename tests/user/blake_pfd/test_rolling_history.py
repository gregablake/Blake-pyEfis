import pytest

from pyefis.user.blake_pfd.core.rolling_history import (
    HistorySample,
    RollingHistory,
)


def test_history_stores_samples() -> None:
    history = RollingHistory(
        window_s=60.0,
    )

    history.add(
        value=100.0,
        timestamp_s=10.0,
    )

    history.add(
        value=105.0,
        timestamp_s=15.0,
    )

    assert history.sample_count == 2
    assert history.samples == (
        HistorySample(
            timestamp_s=10.0,
            value=100.0,
        ),
        HistorySample(
            timestamp_s=15.0,
            value=105.0,
        ),
    )


def test_history_trims_samples_outside_window() -> None:
    history = RollingHistory(
        window_s=10.0,
    )

    history.add(
        value=100.0,
        timestamp_s=0.0,
    )

    history.add(
        value=110.0,
        timestamp_s=5.0,
    )

    history.add(
        value=120.0,
        timestamp_s=11.0,
    )

    assert history.values() == (
        110.0,
        120.0,
    )


def test_sample_exactly_on_cutoff_is_retained() -> None:
    history = RollingHistory(
        window_s=10.0,
    )

    history.add(
        value=100.0,
        timestamp_s=1.0,
    )

    history.add(
        value=110.0,
        timestamp_s=11.0,
    )

    assert history.values() == (
        100.0,
        110.0,
    )


def test_history_reports_duration() -> None:
    history = RollingHistory()

    history.add(
        value=100.0,
        timestamp_s=20.0,
    )

    history.add(
        value=125.0,
        timestamp_s=27.5,
    )

    assert history.duration_s == 7.5


def test_empty_history_properties_are_safe() -> None:
    history = RollingHistory()

    assert history.sample_count == 0
    assert history.oldest is None
    assert history.newest is None
    assert history.duration_s == 0.0
    assert history.values() == ()


def test_clear_removes_all_samples() -> None:
    history = RollingHistory()

    history.add(
        value=100.0,
        timestamp_s=1.0,
    )

    history.clear()

    assert history.sample_count == 0
    assert history.samples == ()


def test_invalid_window_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="window_s",
    ):
        RollingHistory(
            window_s=0.0,
        )