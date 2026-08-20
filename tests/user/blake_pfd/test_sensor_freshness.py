from pyefis.user.blake_pfd.core.sensor_freshness import (
    SensorFreshness,
)


def test_recent_data_is_fresh() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=99.8,
        last_air_data_update=99.7,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is True
    assert state.air_data_fresh is True
    assert state.flight_data_fresh is True
    assert state.message == "FLIGHT DATA FRESH"


def test_stale_attitude_is_detected() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=98.0,
        last_air_data_update=99.8,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is False
    assert state.air_data_fresh is True
    assert state.flight_data_fresh is False
    assert state.message == "STALE: ATTITUDE"


def test_stale_air_data_is_detected() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=99.8,
        last_air_data_update=98.0,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is True
    assert state.air_data_fresh is False
    assert state.flight_data_fresh is False
    assert state.message == "STALE: AIR DATA"


def test_all_stale_sources_are_reported() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=98.0,
        last_air_data_update=98.0,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.flight_data_fresh is False
    assert state.message == "STALE: ATTITUDE / AIR DATA"
    
def test_future_attitude_timestamp_is_stale() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=101.0,
        last_air_data_update=99.5,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is False
    assert state.air_data_fresh is True
    assert state.flight_data_fresh is False
    assert state.message == "STALE: ATTITUDE"


def test_future_air_data_timestamp_is_stale() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=99.5,
        last_air_data_update=101.0,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is True
    assert state.air_data_fresh is False
    assert state.flight_data_fresh is False
    assert state.message == "STALE: AIR DATA"


def test_negative_timeout_fails_safe() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=99.5,
        last_air_data_update=99.5,
        attitude_timeout=-1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is False
    assert state.air_data_fresh is False
    assert state.flight_data_fresh is False
    assert (
        state.message
        == "STALE: ATTITUDE / AIR DATA"
    )


def test_nan_input_fails_safe() -> None:
    state = SensorFreshness().evaluate(
        now=float("nan"),
        last_attitude_update=99.5,
        last_air_data_update=99.5,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is False
    assert state.air_data_fresh is False
    assert state.flight_data_fresh is False
    assert (
        state.message
        == "STALE: ATTITUDE / AIR DATA"
    )


def test_infinite_input_fails_safe() -> None:
    state = SensorFreshness().evaluate(
        now=100.0,
        last_attitude_update=float("inf"),
        last_air_data_update=99.5,
        attitude_timeout=1.0,
        air_data_timeout=1.0,
    )

    assert state.attitude_fresh is False
    assert state.air_data_fresh is False
    assert state.flight_data_fresh is False
    assert (
        state.message
        == "STALE: ATTITUDE / AIR DATA"
    )