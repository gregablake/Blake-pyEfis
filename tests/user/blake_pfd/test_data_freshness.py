from pyefis.user.blake_pfd.core.data_freshness import (
    DataFreshnessMonitor,
)


def test_no_data_is_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    state = monitor.evaluate(
        10.0
    )

    assert state.stale is True
    assert state.fresh is False
    assert state.message == "NO SENSOR DATA"


def test_recent_data_is_fresh() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        10.0
    )

    state = monitor.evaluate(
        10.5
    )

    assert state.fresh is True
    assert state.stale is False
    assert state.age_s == 0.5


def test_old_data_is_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        10.0
    )

    state = monitor.evaluate(
        11.1
    )

    assert state.fresh is False
    assert state.stale is True
    assert state.message == "SENSOR DATA STALE"


def test_backwards_clock_does_not_create_negative_age() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        10.0
    )

    state = monitor.evaluate(
        9.0
    )

    assert state.age_s == 0.0
    assert state.fresh is True