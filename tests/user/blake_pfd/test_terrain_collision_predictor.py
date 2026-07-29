from pyefis.user.blake_pfd.core.terrain_collision_predictor import (
    TerrainCollisionPredictor,
)


def test_safe_clearance():
    predictor = TerrainCollisionPredictor()

    result = predictor.evaluate(
        aircraft_altitude_ft=6500,
        highest_terrain_ft=5000,
    )

    assert result.collision_predicted is False


def test_collision_warning():
    predictor = TerrainCollisionPredictor()

    result = predictor.evaluate(
        aircraft_altitude_ft=5400,
        highest_terrain_ft=5000,
    )

    assert result.collision_predicted is True
    assert result.message == "TERRAIN AHEAD"


def test_exact_clearance():
    predictor = TerrainCollisionPredictor()

    result = predictor.evaluate(
        aircraft_altitude_ft=5500,
        highest_terrain_ft=5000,
    )

    assert result.collision_predicted is False