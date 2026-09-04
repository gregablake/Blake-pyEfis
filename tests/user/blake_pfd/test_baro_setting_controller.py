import math

import pytest

from pyefis.user.blake_pfd.core.baro_setting_controller import (
    BaroSettingController,
)


def test_starts_at_configured_setting():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    assert controller.setting_inhg == 29.92


def test_increment_changes_by_one_hundredth():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    controller.increment()

    assert controller.setting_inhg == 29.93


def test_decrement_changes_by_one_hundredth():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    controller.decrement()

    assert controller.setting_inhg == 29.91


def test_repeated_adjustment_does_not_accumulate_float_error():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    for _ in range(10):
        controller.increment()

    assert controller.setting_inhg == 30.02


def test_upper_limit_is_clamped():
    controller = BaroSettingController(
        initial_inhg=31.50,
    )

    controller.increment()

    assert controller.setting_inhg == 31.50


def test_lower_limit_is_clamped():
    controller = BaroSettingController(
        initial_inhg=27.50,
    )

    controller.decrement()

    assert controller.setting_inhg == 27.50


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        27.49,
        31.51,
    ],
)
def test_invalid_initial_setting_is_rejected(
    value,
):
    with pytest.raises(ValueError):
        BaroSettingController(
            initial_inhg=value,
        )


def test_invalid_runtime_setting_does_not_corrupt_last_valid_value():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    assert controller.set_setting(math.nan) is False
    assert controller.setting_inhg == 29.92


def test_runtime_setting_accepts_valid_value():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    assert controller.set_setting(30.12) is True
    assert controller.setting_inhg == 30.12


def test_runtime_setting_rejects_out_of_range_value():
    controller = BaroSettingController(
        initial_inhg=29.92,
    )

    assert controller.set_setting(32.00) is False
    assert controller.setting_inhg == 29.92
