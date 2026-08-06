from pyefis.user.blake_pfd.core.hits_guidance import (
    HitsGuidance,
)


def test_runtime_guidance_uses_cdi_and_vdi() -> None:
    state = HitsGuidance(
        box_count=6,
    ).calculate(
        cdi=0.5,
        vdi=-0.5,
        navigation_valid=True,
    )

    assert state.valid is True
    assert len(state.boxes) == 6
    assert state.lateral_error == 0.5
    assert state.vertical_error == -0.5


def test_runtime_guidance_hidden_without_position() -> None:
    state = HitsGuidance().calculate(
        cdi=0.0,
        vdi=0.0,
        navigation_valid=False,
    )

    assert state.valid is False
    assert state.boxes == ()


def test_runtime_near_box_moves_more_than_far_box() -> None:
    state = HitsGuidance(
        box_count=6,
    ).calculate(
        cdi=1.0,
        vdi=1.0,
        navigation_valid=True,
    )

    near_box = state.boxes[0]
    far_box = state.boxes[-1]

    assert near_box.center_x_fraction < 0.5
    assert near_box.center_y_fraction > 0.5

    assert far_box.center_x_fraction == 0.5
    assert far_box.center_y_fraction == 0.5


def test_runtime_guidance_stays_centered_on_course() -> None:
    state = HitsGuidance().calculate(
        cdi=0.0,
        vdi=0.0,
        navigation_valid=True,
    )

    for box in state.boxes:
        assert box.center_x_fraction == 0.5
        assert box.center_y_fraction == 0.5