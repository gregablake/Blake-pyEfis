import pytest

from pyefis.user.blake_pfd.core.flight_director import (
    FlightDirector,
)


def test_centered_navigation_produces_zero_commands() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=0.0,
        vdi=0.0,
    )

    assert state.valid is True
    assert state.active is True
    assert state.roll_command_deg == 0.0
    assert state.pitch_command_deg == 0.0


def test_positive_cdi_commands_left_roll() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=0.5,
        vdi=0.0,
    )

    assert state.roll_command_deg < 0.0
    assert state.pitch_command_deg == 0.0


def test_negative_cdi_commands_right_roll() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=-0.5,
        vdi=0.0,
    )

    assert state.roll_command_deg > 0.0


def test_positive_vdi_commands_pitch_down() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=0.0,
        vdi=0.5,
    )

    assert state.pitch_command_deg < 0.0


def test_negative_vdi_commands_pitch_up() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=0.0,
        vdi=-0.5,
    )

    assert state.pitch_command_deg > 0.0


def test_commands_are_limited() -> None:
    director = FlightDirector(
        maximum_roll_command_deg=15.0,
        maximum_pitch_command_deg=7.0,
        lateral_gain=100.0,
        vertical_gain=100.0,
    )

    state = director.calculate(
        cdi=1.0,
        vdi=-1.0,
    )

    assert state.roll_command_deg == -15.0
    assert state.pitch_command_deg == 7.0


def test_errors_are_clamped() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=5.0,
        vdi=-5.0,
    )

    assert state.lateral_error == 1.0
    assert state.vertical_error == -1.0


def test_invalid_navigation_returns_inactive_state() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=0.5,
        vdi=0.5,
        navigation_valid=False,
    )

    assert state.valid is False
    assert state.active is False


def test_disabled_director_returns_inactive_state() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=0.5,
        vdi=0.5,
        enabled=False,
    )

    assert state.valid is False
    assert state.active is False


def test_nonfinite_input_returns_invalid_state() -> None:
    director = FlightDirector()

    state = director.calculate(
        cdi=float("nan"),
        vdi=0.0,
    )

    assert state.valid is False


def test_small_commands_are_removed_by_deadband() -> None:
    director = FlightDirector(
        lateral_gain=1.0,
        vertical_gain=1.0,
        command_deadband=0.1,
    )

    state = director.calculate(
        cdi=0.05,
        vdi=-0.05,
    )

    assert state.roll_command_deg == 0.0
    assert state.pitch_command_deg == 0.0


def test_constructor_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        FlightDirector(
            maximum_roll_command_deg=0.0,
        )

    with pytest.raises(ValueError):
        FlightDirector(
            maximum_pitch_command_deg=-1.0,
        )

    with pytest.raises(ValueError):
        FlightDirector(
            command_deadband=-0.1,
        )