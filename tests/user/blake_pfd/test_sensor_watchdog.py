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