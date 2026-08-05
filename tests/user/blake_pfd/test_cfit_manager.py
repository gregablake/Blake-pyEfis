from types import SimpleNamespace

from pyefis.user.blake_pfd.core.cfit_manager import (
    CfitManager,
)


def profile():
    return SimpleNamespace(
        points=[
            SimpleNamespace(
                distance_nm=2,
                elevation_ft=3500,
            )
        ]
    )


def test_update_returns_valid_state():

    manager = CfitManager()

    state = manager.update(
        aircraft_altitude_ft=3000,
        vertical_speed_fpm=-1000,
        ground_speed_kt=120,
        terrain_profile=profile(),
    )

    assert state.valid
    assert state.prediction.collision_predicted


def test_clear():

    manager = CfitManager()

    manager.update(
        aircraft_altitude_ft=3000,
        vertical_speed_fpm=-1000,
        ground_speed_kt=120,
        terrain_profile=profile(),
    )

    manager.clear()

    assert manager.state.valid is False