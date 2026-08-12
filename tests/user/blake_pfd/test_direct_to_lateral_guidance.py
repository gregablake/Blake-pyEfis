import pytest
from types import SimpleNamespace

from pyefis.user.blake_pfd.core.direct_to_lateral_guidance import (
    DirectToLateralGuidance,
)


def make_guidance(
    course_error_deg: float,
):
    return SimpleNamespace(
        active=True,
        course_error_deg=course_error_deg,
    )


def test_inactive_guidance_returns_inactive() -> None:
    adapter = DirectToLateralGuidance()

    state = adapter.update(
        guidance_state=SimpleNamespace(
            active=False,
        )
    )

    assert state.active is False


def test_on_course_returns_zero_error() -> None:
    adapter = DirectToLateralGuidance()

    state = adapter.update(
        guidance_state=make_guidance(
            0.0
        )
    )

    assert state.active is True
    assert state.lateral_error == 0.0


def test_target_right_produces_negative_lateral_error() -> None:
    adapter = DirectToLateralGuidance(
        full_scale_error_deg=20.0,
    )

    state = adapter.update(
        guidance_state=make_guidance(
            10.0
        )
    )

    assert state.lateral_error == -0.5


def test_target_left_produces_positive_lateral_error() -> None:
    adapter = DirectToLateralGuidance(
        full_scale_error_deg=20.0,
    )

    state = adapter.update(
        guidance_state=make_guidance(
            -10.0
        )
    )

    assert state.lateral_error == 0.5


def test_error_is_clamped() -> None:
    adapter = DirectToLateralGuidance(
        full_scale_error_deg=20.0,
    )

    right = adapter.update(
        guidance_state=make_guidance(
            90.0
        )
    )

    assert right.lateral_error == -1.0

    left = adapter.update(
        guidance_state=make_guidance(
            -90.0
        )
    )

    assert left.lateral_error == 1.0


def test_invalid_course_error_clears() -> None:
    adapter = DirectToLateralGuidance()

    state = adapter.update(
        guidance_state=SimpleNamespace(
            active=True,
            course_error_deg=None,
        )
    )

    assert state.active is False


def test_invalid_full_scale_raises() -> None:
    with pytest.raises(ValueError):
        DirectToLateralGuidance(
            full_scale_error_deg=0.0,
        )