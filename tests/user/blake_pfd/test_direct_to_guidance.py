from types import SimpleNamespace

from pyefis.user.blake_pfd.core.direct_to_guidance import (
    DirectToGuidance,
)


def make_direct_to(
    *,
    bearing_deg: float,
    distance_nm: float = 10.0,
):
    return SimpleNamespace(
        active=True,
        identifier="KHAO",
        bearing_deg=bearing_deg,
        distance_nm=distance_nm,
    )


def test_guidance_starts_inactive() -> None:
    guidance = DirectToGuidance()

    assert guidance.state.active is False


def test_on_course_has_zero_error() -> None:
    guidance = DirectToGuidance()

    state = guidance.update(
        direct_to_state=make_direct_to(
            bearing_deg=90.0,
        ),
        aircraft_track_deg=90.0,
    )

    assert state.active is True
    assert state.identifier == "KHAO"
    assert state.course_error_deg == 0.0


def test_target_right_of_track_is_positive() -> None:
    guidance = DirectToGuidance()

    state = guidance.update(
        direct_to_state=make_direct_to(
            bearing_deg=100.0,
        ),
        aircraft_track_deg=90.0,
    )

    assert state.course_error_deg == 10.0


def test_target_left_of_track_is_negative() -> None:
    guidance = DirectToGuidance()

    state = guidance.update(
        direct_to_state=make_direct_to(
            bearing_deg=80.0,
        ),
        aircraft_track_deg=90.0,
    )

    assert state.course_error_deg == -10.0


def test_course_error_wraps_across_north() -> None:
    guidance = DirectToGuidance()

    state = guidance.update(
        direct_to_state=make_direct_to(
            bearing_deg=5.0,
        ),
        aircraft_track_deg=355.0,
    )

    assert state.course_error_deg == 10.0


def test_inactive_direct_to_clears_guidance() -> None:
    guidance = DirectToGuidance()

    direct_to = SimpleNamespace(
        active=False,
    )

    state = guidance.update(
        direct_to_state=direct_to,
        aircraft_track_deg=90.0,
    )

    assert state.active is False


def test_invalid_track_clears_guidance() -> None:
    guidance = DirectToGuidance()

    state = guidance.update(
        direct_to_state=make_direct_to(
            bearing_deg=90.0,
        ),
        aircraft_track_deg=None,
    )

    assert state.active is False