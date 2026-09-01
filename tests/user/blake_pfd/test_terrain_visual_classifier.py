from __future__ import annotations

from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
    TerrainSurfaceVertex,
    TerrainTriangle,
)
from pyefis.user.blake_pfd.core.terrain_visual_classifier import (
    TerrainVisualClassifier,
)


def surface_at_elevation(
    elevation_ft: float,
) -> TerrainSurface:
    return TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=6076.12,
                east_ft=-100.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=elevation_ft,
            ),
            TerrainSurfaceVertex(
                north_ft=6076.12,
                east_ft=100.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=elevation_ft,
            ),
            TerrainSurfaceVertex(
                north_ft=12152.24,
                east_ft=0.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=elevation_ft,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )


def classify(
    elevation_ft: float,
    *,
    altitude_ft: float = 2000.0,
    vertical_speed_fpm: float = 0.0,
    ground_speed_kt: float = 120.0,
):
    return TerrainVisualClassifier().classify(
        surface=surface_at_elevation(
            elevation_ft
        ),
        aircraft_altitude_ft=altitude_ft,
        vertical_speed_fpm=vertical_speed_fpm,
        ground_speed_kt=ground_speed_kt,
    )


def test_safe_terrain_is_none() -> None:
    result = classify(
        elevation_ft=500.0,
    )

    assert result.valid is True
    assert len(result.triangles) == 1
    assert result.triangles[0].warning_level == "NONE"


def test_terrain_within_1000_ft_is_caution() -> None:
    result = classify(
        elevation_ft=1100.0,
    )

    assert result.valid is True
    assert (
        result.triangles[0].warning_level
        == "CAUTION"
    )


def test_terrain_within_500_ft_is_warning() -> None:
    result = classify(
        elevation_ft=1600.0,
    )

    assert result.valid is True
    assert (
        result.triangles[0].warning_level
        == "WARNING"
    )


def test_terrain_within_100_ft_is_critical() -> None:
    result = classify(
        elevation_ft=1950.0,
    )

    assert result.valid is True
    assert (
        result.triangles[0].warning_level
        == "CRITICAL"
    )


def test_descent_can_raise_visual_warning_level() -> None:
    level = classify(
        elevation_ft=900.0,
        altitude_ft=2000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=120.0,
    )

    descending = classify(
        elevation_ft=900.0,
        altitude_ft=2000.0,
        vertical_speed_fpm=-1000.0,
        ground_speed_kt=120.0,
    )

    assert (
        level.triangles[0].warning_level
        == "NONE"
    )

    assert (
        descending.triangles[0].warning_level
        != "NONE"
    )


def test_invalid_surface_fails_closed() -> None:
    result = TerrainVisualClassifier().classify(
        surface=TerrainSurface(
            valid=False,
        ),
        aircraft_altitude_ft=2000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=120.0,
    )

    assert result.valid is False
    assert result.triangles == ()
    assert result.message == (
        "TERRAIN SURFACE INVALID"
    )


def test_shared_vertices_are_classified_once_per_call() -> None:
    from types import SimpleNamespace

    evaluation_calls = 0

    class CountingAwareness:
        def evaluate(self, **kwargs):
            nonlocal evaluation_calls
            evaluation_calls += 1

            return SimpleNamespace(
                valid=True,
                warning_level="NONE",
            )

    surface = TerrainSurface(
        vertices=(
            TerrainSurfaceVertex(
                north_ft=6076.12,
                east_ft=-100.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=500.0,
            ),
            TerrainSurfaceVertex(
                north_ft=6076.12,
                east_ft=100.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=500.0,
            ),
            TerrainSurfaceVertex(
                north_ft=12152.24,
                east_ft=-100.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=500.0,
            ),
            TerrainSurfaceVertex(
                north_ft=12152.24,
                east_ft=100.0,
                up_ft=0.0,
                latitude_deg=39.0,
                longitude_deg=-84.0,
                elevation_ft=500.0,
            ),
        ),
        triangles=(
            TerrainTriangle(
                first_index=0,
                second_index=1,
                third_index=2,
            ),
            TerrainTriangle(
                first_index=1,
                second_index=3,
                third_index=2,
            ),
        ),
        rows=2,
        columns=2,
        valid=True,
    )

    result = TerrainVisualClassifier(
        awareness=CountingAwareness(),
    ).classify(
        surface=surface,
        aircraft_altitude_ft=2000.0,
        vertical_speed_fpm=0.0,
        ground_speed_kt=120.0,
    )

    assert result.valid is True
    assert len(result.triangles) == 2
    assert evaluation_calls == 4
