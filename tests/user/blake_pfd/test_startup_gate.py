from pyefis.user.blake_pfd.core.startup_gate import (
    StartupGate,
)


def test_config_failure_blocks_startup() -> None:
    state = StartupGate().evaluate(
        config_ok=False,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        hardware_mode=True,
    )

    assert state.blocked is True
    assert state.ready is False
    assert state.message == "STARTUP BLOCKED: CONFIG"


def test_database_failure_blocks_startup() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=False,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        hardware_mode=True,
    )

    assert state.blocked is True
    assert state.ready is False
    assert state.message == "STARTUP BLOCKED: DATABASE"


def test_waits_for_first_flight_data() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=False,
        attitude_valid=False,
        air_data_valid=False,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert state.message == "INITIALIZING FLIGHT DATA"


def test_hardware_waits_for_ahrs_and_air_data() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=False,
        air_data_valid=False,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert state.message == "INITIALIZING: AHRS / AIR DATA"


def test_hardware_ready_when_required_data_valid() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        hardware_mode=True,
    )

    assert state.ready is True
    assert state.message == "SYSTEM READY"


def test_simulator_does_not_require_real_hardware() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=False,
        air_data_valid=False,
        hardware_mode=False,
    )

    assert state.ready is True
    
def test_hardware_waits_for_fresh_attitude_data() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=False,
        air_data_fresh=True,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert state.message == "INITIALIZING: AHRS STALE"


def test_hardware_waits_for_fresh_air_data() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=True,
        air_data_fresh=False,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert state.message == "INITIALIZING: AIR DATA STALE"
    
def test_hardware_stale_attitude_reports_stale() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=False,
        air_data_fresh=True,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert (
        state.message
        == "INITIALIZING: AHRS STALE"
    )


def test_hardware_failed_attitude_reports_ahrs() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=False,
        air_data_valid=True,
        attitude_fresh=False,
        air_data_fresh=True,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert (
        state.message
        == "INITIALIZING: AHRS"
    )


def test_hardware_stale_air_data_reports_stale() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=True,
        attitude_fresh=True,
        air_data_fresh=False,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert (
        state.message
        == "INITIALIZING: AIR DATA STALE"
    )


def test_hardware_failed_air_data_reports_air_data() -> None:
    state = StartupGate().evaluate(
        config_ok=True,
        database_ok=True,
        flight_data_available=True,
        attitude_valid=True,
        air_data_valid=False,
        attitude_fresh=True,
        air_data_fresh=False,
        hardware_mode=True,
    )

    assert state.initializing is True
    assert state.ready is False
    assert (
        state.message
        == "INITIALIZING: AIR DATA"
    )