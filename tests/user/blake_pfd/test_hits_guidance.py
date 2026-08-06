import pytest

from pyefis.user.blake_pfd.core.hits_guidance import (
    HitsGuidance,
)


def test_centered_guidance_creates_centered_boxes() -> None:
    guidance = HitsGuidance(
        box_count=4,
    )

    state = guidance.calculate(
        cdi=0.0,
        vdi=0.0,
    )

    assert state.valid is True
    assert len(state.boxes) == 4

    for box in state.boxes:
        assert box.center_x_fraction == pytest.approx(
            0.5
        )
        assert box.center_y_fraction == pytest.approx(
            0.5
        )


def test_boxes_shrink_into_distance() -> None:
    guidance = HitsGuidance(
        box_count=4,
    )

    state = guidance.calculate(
        cdi=0.0,
        vdi=0.0,
    )

    assert (
        state.boxes[0].width_fraction
        > state.boxes[-1].width_fraction
    )
    assert (
        state.boxes[0].height_fraction
        > state.boxes[-1].height_fraction
    )


def test_positive_cdi_moves_near_boxes_left() -> None:
    guidance = HitsGuidance(
        box_count=4,
    )

    state = guidance.calculate(
        cdi=1.0,
        vdi=0.0,
    )

    assert (
        state.boxes[0].center_x_fraction
        < 0.5
    )
    assert (
        state.boxes[-1].center_x_fraction
        == pytest.approx(
            0.5
        )
    )


def test_negative_cdi_moves_near_boxes_right() -> None:
    guidance = HitsGuidance()

    state = guidance.calculate(
        cdi=-1.0,
        vdi=0.0,
    )

    assert (
        state.boxes[0].center_x_fraction
        > 0.5
    )


def test_positive_vdi_moves_near_boxes_down() -> None:
    guidance = HitsGuidance()

    state = guidance.calculate(
        cdi=0.0,
        vdi=1.0,
    )

    assert (
        state.boxes[0].center_y_fraction
        > 0.5
    )


def test_errors_are_clamped() -> None:
    guidance = HitsGuidance()

    state = guidance.calculate(
        cdi=5.0,
        vdi=-5.0,
    )

    assert state.lateral_error == 1.0
    assert state.vertical_error == -1.0


def test_invalid_navigation_returns_invalid_state() -> None:
    guidance = HitsGuidance()

    state = guidance.calculate(
        cdi=0.0,
        vdi=0.0,
        navigation_valid=False,
    )

    assert state.valid is False
    assert state.boxes == ()


def test_nonfinite_input_returns_invalid_state() -> None:
    guidance = HitsGuidance()

    state = guidance.calculate(
        cdi=float("nan"),
        vdi=0.0,
    )

    assert state.valid is False


def test_constructor_rejects_too_few_boxes() -> None:
    with pytest.raises(ValueError):
        HitsGuidance(
            box_count=1,
        )


def test_constructor_rejects_bad_box_sizes() -> None:
    with pytest.raises(ValueError):
        HitsGuidance(
            near_width_fraction=0.1,
            far_width_fraction=0.2,
        )

    with pytest.raises(ValueError):
        HitsGuidance(
            near_height_fraction=0.1,
            far_height_fraction=0.2,
        )