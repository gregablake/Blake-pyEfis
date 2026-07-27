import pytest

from pyefis.user.blake_pfd.core.aircraft_performance_config import (
    AircraftPerformanceConfig,
)


def test_default_performance_configuration() -> None:
    config = AircraftPerformanceConfig()

    assert config.best_glide_speed_kt == 80.0
    assert config.glide_ratio == 9.0
    assert config.glide_reserve_altitude_ft == 1000.0


def test_custom_performance_configuration() -> None:
    config = AircraftPerformanceConfig(
        best_glide_speed_kt=92.0,
        glide_ratio=10.5,
        glide_reserve_altitude_ft=750.0,
    )

    assert config.best_glide_speed_kt == 92.0
    assert config.glide_ratio == 10.5
    assert config.glide_reserve_altitude_ft == 750.0


def test_invalid_best_glide_speed_raises() -> None:
    with pytest.raises(
        ValueError,
        match="best_glide_speed_kt",
    ):
        AircraftPerformanceConfig(
            best_glide_speed_kt=0.0,
        )


def test_invalid_glide_ratio_raises() -> None:
    with pytest.raises(
        ValueError,
        match="glide_ratio",
    ):
        AircraftPerformanceConfig(
            glide_ratio=float("nan"),
        )


def test_negative_reserve_altitude_raises() -> None:
    with pytest.raises(
        ValueError,
        match="glide_reserve_altitude_ft",
    ):
        AircraftPerformanceConfig(
            glide_reserve_altitude_ft=-1.0,
        )