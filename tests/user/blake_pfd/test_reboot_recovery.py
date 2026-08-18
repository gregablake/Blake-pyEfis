from pyefis.user.blake_pfd.core.reboot_recovery import (
    RebootRecovery,
)


def test_normal_clean_startup() -> None:
    state = RebootRecovery().evaluate(
        previous_shutdown_clean=True,
        startup_ready=True,
        flight_data_valid=True,
    )

    assert state.recovery_required is False
    assert state.inhibit_ready is False
    assert state.message == "NORMAL STARTUP"


def test_clean_startup_waits_for_readiness() -> None:
    state = RebootRecovery().evaluate(
        previous_shutdown_clean=True,
        startup_ready=False,
        flight_data_valid=False,
    )

    assert state.recovery_required is False
    assert state.inhibit_ready is True
    assert state.message == "STARTUP CHECK IN PROGRESS"


def test_unclean_restart_without_flight_data() -> None:
    state = RebootRecovery().evaluate(
        previous_shutdown_clean=False,
        startup_ready=False,
        flight_data_valid=False,
    )

    assert state.recovery_required is True
    assert state.inhibit_ready is True
    assert (
        state.message
        == "UNCLEAN RESTART - WAITING FOR FLIGHT DATA"
    )


def test_unclean_restart_requires_system_recheck() -> None:
    state = RebootRecovery().evaluate(
        previous_shutdown_clean=False,
        startup_ready=False,
        flight_data_valid=True,
    )

    assert state.recovery_required is True
    assert state.inhibit_ready is True
    assert (
        state.message
        == "UNCLEAN RESTART - SYSTEM RECHECK"
    )


def test_unclean_restart_can_recover() -> None:
    state = RebootRecovery().evaluate(
        previous_shutdown_clean=False,
        startup_ready=True,
        flight_data_valid=True,
    )

    assert state.recovery_required is True
    assert state.inhibit_ready is False
    assert (
        state.message
        == "RECOVERED AFTER UNCLEAN RESTART"
    )