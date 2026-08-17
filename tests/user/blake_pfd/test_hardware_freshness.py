from __future__ import annotations

from pyefis.user.blake_pfd.core.data_freshness import (
    DataFreshnessMonitor,
)


def test_ahrs_can_be_ok_but_stale() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=0.5,
    )

    hardware_ok = True

    monitor.mark_update(
        10.0
    )

    freshness = monitor.evaluate(
        10.6
    )

    attitude_valid = (
        hardware_ok
        and freshness.fresh
    )

    assert hardware_ok is True
    assert freshness.stale is True
    assert attitude_valid is False


def test_fresh_ahrs_remains_valid() -> None:
    monitor = DataFreshnessMonitor(
        stale_after_s=0.5,
    )

    hardware_ok = True

    monitor.mark_update(
        10.0
    )

    freshness = monitor.evaluate(
        10.2
    )

    attitude_valid = (
        hardware_ok
        and freshness.fresh
    )

    assert freshness.fresh is True
    assert attitude_valid is True


def test_stale_baro_invalidates_air_data() -> None:
    baro = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    airspeed = DataFreshnessMonitor(
        stale_after_s=1.0,
    )

    baro.mark_update(
        10.0
    )

    airspeed.mark_update(
        10.8
    )

    baro_state = baro.evaluate(
        11.1
    )

    airspeed_state = airspeed.evaluate(
        11.1
    )

    air_data_valid = (
        baro_state.fresh
        and airspeed_state.fresh
    )

    assert baro_state.stale is True
    assert airspeed_state.fresh is True
    assert air_data_valid is False


def test_stale_gps_invalidates_position() -> None:
    gps = DataFreshnessMonitor(
        stale_after_s=2.5,
    )

    hardware_gps_ok = True
    flight_position_valid = True

    gps.mark_update(
        10.0
    )

    freshness = gps.evaluate(
        12.6
    )

    position_valid = (
        hardware_gps_ok
        and freshness.fresh
        and flight_position_valid
    )

    assert hardware_gps_ok is True
    assert flight_position_valid is True
    assert freshness.stale is True
    assert position_valid is False