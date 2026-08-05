from types import SimpleNamespace

from pyefis.user.blake_pfd.core.cfit_predictor import (
    CfitPredictor,
)


def profile(*pairs):
    return SimpleNamespace(
        points=[
            SimpleNamespace(
                distance_nm=d,
                elevation_ft=e,
            )
            for d, e in pairs
        ]
    )


def test_no_collision():
    prediction = (
        CfitPredictor().predict(
            aircraft_altitude_ft=5000,
            vertical_speed_fpm=0,
            ground_speed_kt=100,
            terrain_profile=profile(
                (2,2500),
                (5,2600),
            ),
        )
    )

    assert prediction.collision_predicted is False


def test_collision():
    prediction = (
        CfitPredictor().predict(
            aircraft_altitude_ft=3000,
            vertical_speed_fpm=-1000,
            ground_speed_kt=120,
            terrain_profile=profile(
                (3,3200),
            ),
        )
    )

    assert prediction.collision_predicted
    assert prediction.seconds_to_collision > 0
    assert prediction.message == "CFIT PREDICTED"


def test_empty_profile():
    prediction = (
        CfitPredictor().predict(
            aircraft_altitude_ft=4000,
            vertical_speed_fpm=0,
            ground_speed_kt=100,
            terrain_profile=profile(),
        )
    )

    assert prediction.collision_predicted is False