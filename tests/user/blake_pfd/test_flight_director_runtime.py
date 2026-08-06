from pyefis.user.blake_pfd.core.flight_director import (
    FlightDirector,
)


def test_runtime_director_uses_cdi_and_vdi() -> None:
    state = FlightDirector().calculate(
        cdi=0.5,
        vdi=-0.5,
        navigation_valid=True,
        enabled=True,
    )

    assert state.valid is True
    assert state.active is True
    assert state.roll_command_deg < 0.0
    assert state.pitch_command_deg > 0.0


def test_runtime_director_hidden_without_position() -> None:
    state = FlightDirector().calculate(
        cdi=0.5,
        vdi=0.5,
        navigation_valid=False,
        enabled=True,
    )

    assert state.valid is False
    assert state.active is False


def test_runtime_director_hidden_when_disabled() -> None:
    state = FlightDirector().calculate(
        cdi=0.5,
        vdi=0.5,
        navigation_valid=True,
        enabled=False,
    )

    assert state.valid is False
    assert state.active is False


def test_runtime_director_centered_on_course() -> None:
    state = FlightDirector().calculate(
        cdi=0.0,
        vdi=0.0,
        navigation_valid=True,
        enabled=True,
    )

    assert state.valid is True
    assert state.roll_command_deg == 0.0
    assert state.pitch_command_deg == 0.0