from pyefis.user.blake_pfd.core.sensor_watchdog import (
    SensorWatchdog,
)


def test_all_sensors_healthy() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=True,
        attitude_valid=True,
        air_data_valid=True,
    )

    assert state.failed is False
    assert state.degraded is False
    assert state.message == "SENSORS OK"


def test_complete_flight_data_loss() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=False,
        position_valid=False,
    )

    assert state.failed is True
    assert state.degraded is False
    assert state.message == "FLIGHT DATA LOST"


def test_gps_loss_is_degraded() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=False,
        attitude_valid=True,
        air_data_valid=True,
    )

    assert state.failed is False
    assert state.degraded is True
    assert state.message == "DEGRADED: GPS"


def test_multiple_sensor_failures() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=False,
        attitude_valid=False,
        air_data_valid=False,
    )

    assert state.failed is False
    assert state.degraded is True
    assert (
        state.message
        == "DEGRADED: ATTITUDE / AIR DATA / GPS"
    )

def test_healthy_but_stale_attitude_reports_stale() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=True,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=False,
        air_data_fresh=True,
    )

    assert state.degraded is True
    assert state.failed is False
    assert (
        state.message
        == "DEGRADED: ATTITUDE STALE"
    )


def test_failed_attitude_does_not_also_report_stale() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=True,
        attitude_valid=False,
        air_data_valid=True,
        attitude_fresh=False,
        air_data_fresh=True,
    )

    assert state.degraded is True
    assert state.failed is False
    assert (
        state.message
        == "DEGRADED: ATTITUDE"
    )

def test_healthy_but_stale_air_data_reports_stale() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=True,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=True,
        air_data_fresh=False,
    )

    assert state.degraded is True
    assert state.failed is False
    assert (
        state.message
        == "DEGRADED: AIR DATA STALE"
    )


def test_failed_air_data_does_not_also_report_stale() -> None:
    state = SensorWatchdog().evaluate(
        flight_data_available=True,
        position_valid=True,
        attitude_valid=True,
        air_data_valid=False,
        attitude_fresh=True,
        air_data_fresh=False,
    )

    assert state.degraded is True
    assert state.failed is False
    assert (
        state.message
        == "DEGRADED: AIR DATA"
    )

def test_stale_position_reports_gps_stale() -> None:
    watchdog = SensorWatchdog()

    state = watchdog.evaluate(
        flight_data_available=True,
        position_valid=True,
        position_fresh=False,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=True,
        air_data_fresh=True,
    )

    assert state.position_valid is True
    assert state.position_fresh is False
    assert state.degraded is True
    assert state.failed is False
    assert (
        state.message
        == "DEGRADED: GPS STALE"
    )


def test_invalid_position_takes_priority_over_stale() -> None:
    watchdog = SensorWatchdog()

    state = watchdog.evaluate(
        flight_data_available=True,
        position_valid=False,
        position_fresh=False,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=True,
        air_data_fresh=True,
    )

    assert state.position_valid is False
    assert state.position_fresh is False
    assert state.degraded is True
    assert state.failed is False
    assert (
        state.message
        == "DEGRADED: GPS"
    )
