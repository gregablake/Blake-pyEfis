import pytest

from pyefis.user.blake_pfd.airdata_calculations import (
    indicated_altitude,
)


def test_standard_setting_matches_pressure_altitude() -> None:
    altitude_ft = indicated_altitude(
        static_pa=101325.0,
        baro_setting_inhg=29.92,
    )

    assert altitude_ft == pytest.approx(
        0.0,
        abs=2.0,
    )


def test_higher_altimeter_setting_increases_indicated_altitude() -> None:
    standard_ft = indicated_altitude(
        static_pa=101325.0,
        baro_setting_inhg=29.92,
    )

    high_setting_ft = indicated_altitude(
        static_pa=101325.0,
        baro_setting_inhg=30.12,
    )

    assert high_setting_ft > standard_ft
    assert high_setting_ft == pytest.approx(
        183.0,
        abs=3.0,
    )


def test_lower_altimeter_setting_decreases_indicated_altitude() -> None:
    altitude_ft = indicated_altitude(
        static_pa=101325.0,
        baro_setting_inhg=29.72,
    )

    assert altitude_ft == pytest.approx(
        -187.0,
        abs=3.0,
    )


@pytest.mark.parametrize(
    "baro_setting_inhg",
    [
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_invalid_altimeter_setting_fails_closed(
    baro_setting_inhg: float,
) -> None:
    with pytest.raises(ValueError):
        indicated_altitude(
            static_pa=101325.0,
            baro_setting_inhg=baro_setting_inhg,
        )
