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


def test_backwards_clock_is_fail_safe_stale() -> None:
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
    assert state.fresh is False
    assert state.stale is True
    assert (
        state.message
        == "SENSOR DATA STALE"
    )
    
def test_nan_current_time_is_fail_safe_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        10.0
    )

    state = monitor.evaluate(
        float("nan")
    )

    assert state.fresh is False
    assert state.stale is True
    assert (
        state.message
        == "SENSOR DATA STALE"
    )


def test_infinite_current_time_is_fail_safe_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        10.0
    )

    state = monitor.evaluate(
        float("inf")
    )

    assert state.fresh is False
    assert state.stale is True
    assert (
        state.message
        == "SENSOR DATA STALE"
    )


def test_nan_update_timestamp_is_fail_safe_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        float("nan")
    )

    state = monitor.evaluate(
        10.0
    )

    assert state.fresh is False
    assert state.stale is True
    assert (
        state.message
        == "SENSOR DATA STALE"
    )


def test_infinite_update_timestamp_is_fail_safe_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    monitor.mark_update(
        float("inf")
    )

    state = monitor.evaluate(
        10.0
    )

    assert state.fresh is False
    assert state.stale is True
    assert (
        state.message
        == "SENSOR DATA STALE"
    )