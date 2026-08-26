from pathlib import Path
from struct import pack

import pytest

from pyefis.user.blake_pfd.core.srtm_terrain_source import (
    METERS_TO_FEET,
    SrtmTerrainSource,
)


def write_test_tile(
    directory: Path,
    *,
    tile_name: str,
    samples_per_side: int,
    default_elevation_m: int = 100,
    overrides: dict[
        tuple[int, int],
        int,
    ] | None = None,
) -> Path:
    values = [
        default_elevation_m
    ] * (
        samples_per_side
        * samples_per_side
    )

    for (
        row,
        column,
    ), elevation_m in (
        overrides or {}
    ).items():
        index = (
            row
            * samples_per_side
            + column
        )
        values[index] = elevation_m

    data = b"".join(
        pack(
            ">h",
            value,
        )
        for value in values
    )

    path = directory / f"{tile_name}.hgt"
    path.write_bytes(data)

    return path


def test_tile_name_northern_western() -> None:
    assert (
        SrtmTerrainSource.tile_name(
            39,
            -85,
        )
        == "N39W085"
    )


def test_tile_name_southern_eastern() -> None:
    assert (
        SrtmTerrainSource.tile_name(
            -12,
            44,
        )
        == "S12E044"
    )


def test_reads_elevation_from_tile(
    tmp_path: Path,
) -> None:
    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=250,
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    elevation_ft = source.get_elevation(
        39.5,
        -84.5,
    )

    assert elevation_ft == pytest.approx(
        250.0 * METERS_TO_FEET
    )


def test_reads_specific_sample(
    tmp_path: Path,
) -> None:
    maximum_index = 1200

    latitude = 39.75
    longitude = -84.25

    expected_row = int(
        round(
            (1.0 - 0.75)
            * maximum_index
        )
    )

    expected_column = int(
        round(
            0.75
            * maximum_index
        )
    )

    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
        overrides={
            (
                expected_row,
                expected_column,
            ): 500,
        },
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    elevation_ft = source.get_elevation(
        latitude,
        longitude,
    )

    assert elevation_ft == pytest.approx(
        500.0 * METERS_TO_FEET
    )


def test_missing_tile_returns_none(
    tmp_path: Path,
) -> None:
    source = SrtmTerrainSource(
        tmp_path
    )

    assert source.get_elevation(
        39.5,
        -84.5,
    ) is None


def test_void_elevation_returns_none(
    tmp_path: Path,
) -> None:
    maximum_index = 1200

    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
        overrides={
            (
                maximum_index // 2,
                maximum_index // 2,
            ): -32768,
        },
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    assert source.get_elevation(
        39.5,
        -84.5,
    ) is None


def test_invalid_tile_size_returns_none(
    tmp_path: Path,
) -> None:
    path = tmp_path / "N39W085.hgt"
    path.write_bytes(
        b"not-a-valid-hgt-file"
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    assert source.get_elevation(
        39.5,
        -84.5,
    ) is None


def test_invalid_coordinates_return_none(
    tmp_path: Path,
) -> None:
    source = SrtmTerrainSource(
        tmp_path
    )

    assert source.get_elevation(
        91.0,
        -84.0,
    ) is None

    assert source.get_elevation(
        39.0,
        -181.0,
    ) is None


def test_callable_interface(
    tmp_path: Path,
) -> None:
    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=200,
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    assert source(
        39.5,
        -84.5,
    ) == pytest.approx(
        200.0 * METERS_TO_FEET
    )


def test_cache_reuses_loaded_tile(
    tmp_path: Path,
) -> None:
    tile_path = write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    first = source.get_elevation(
        39.2,
        -84.8,
    )

    tile_path.unlink()

    second = source.get_elevation(
        39.8,
        -84.2,
    )

    assert first == pytest.approx(
        100.0 * METERS_TO_FEET
    )
    assert second == pytest.approx(
        100.0 * METERS_TO_FEET
    )


def test_bilinear_interpolates_between_four_samples(
    tmp_path: Path,
) -> None:
    maximum_index = 1200

    row_position = 600.5
    column_position = 600.5

    latitude_fraction = (
        1.0
        - row_position / maximum_index
    )

    longitude_fraction = (
        column_position / maximum_index
    )

    latitude = (
        39.0
        + latitude_fraction
    )

    longitude = (
        -85.0
        + longitude_fraction
    )

    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=0,
        overrides={
            (600, 600): 100,
            (600, 601): 200,
            (601, 600): 300,
            (601, 601): 400,
        },
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    elevation_ft = source.get_elevation(
        latitude,
        longitude,
    )

    assert elevation_ft == pytest.approx(
        250.0 * METERS_TO_FEET
    )


def test_bilinear_required_void_sample_fails_closed(
    tmp_path: Path,
) -> None:
    maximum_index = 1200

    row_position = 600.5
    column_position = 600.5

    latitude = (
        39.0
        + (
            1.0
            - row_position / maximum_index
        )
    )

    longitude = (
        -85.0
        + column_position / maximum_index
    )

    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
        overrides={
            (600, 600): 100,
            (600, 601): 200,
            (601, 600): 300,
            (601, 601): -32768,
        },
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    assert source.get_elevation(
        latitude,
        longitude,
    ) is None


def test_exact_grid_sample_does_not_require_neighbor(
    tmp_path: Path,
) -> None:
    maximum_index = 1200

    row = 600
    column = 600

    latitude = (
        39.0
        + (
            1.0
            - row / maximum_index
        )
    )

    longitude = (
        -85.0
        + column / maximum_index
    )

    write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
        overrides={
            (600, 600): 500,
            (600, 601): -32768,
            (601, 600): -32768,
            (601, 601): -32768,
        },
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    assert source.get_elevation(
        latitude,
        longitude,
    ) == pytest.approx(
        500.0 * METERS_TO_FEET
    )


def test_cache_retains_multiple_loaded_tiles(
    tmp_path: Path,
) -> None:
    first_path = write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
    )

    second_path = write_test_tile(
        tmp_path,
        tile_name="N39W084",
        samples_per_side=1201,
        default_elevation_m=200,
    )

    source = SrtmTerrainSource(
        tmp_path
    )

    first = source.get_elevation(
        39.5,
        -84.5,
    )

    second = source.get_elevation(
        39.5,
        -83.5,
    )

    first_path.unlink()
    second_path.unlink()

    first_again = source.get_elevation(
        39.5,
        -84.5,
    )

    second_again = source.get_elevation(
        39.5,
        -83.5,
    )

    assert first == pytest.approx(
        100.0 * METERS_TO_FEET
    )
    assert second == pytest.approx(
        200.0 * METERS_TO_FEET
    )
    assert first_again == pytest.approx(
        100.0 * METERS_TO_FEET
    )
    assert second_again == pytest.approx(
        200.0 * METERS_TO_FEET
    )


def test_lru_cache_evicts_oldest_tile(
    tmp_path: Path,
) -> None:
    first_path = write_test_tile(
        tmp_path,
        tile_name="N39W085",
        samples_per_side=1201,
        default_elevation_m=100,
    )

    second_path = write_test_tile(
        tmp_path,
        tile_name="N39W084",
        samples_per_side=1201,
        default_elevation_m=200,
    )

    third_path = write_test_tile(
        tmp_path,
        tile_name="N39W083",
        samples_per_side=1201,
        default_elevation_m=300,
    )

    source = SrtmTerrainSource(
        tmp_path,
        cache_size=2,
    )

    assert source.get_elevation(
        39.5,
        -84.5,
    ) is not None

    assert source.get_elevation(
        39.5,
        -83.5,
    ) is not None

    # Touch the first tile so the second becomes LRU.
    assert source.get_elevation(
        39.5,
        -84.5,
    ) is not None

    assert source.get_elevation(
        39.5,
        -82.5,
    ) is not None

    first_path.unlink()
    second_path.unlink()
    third_path.unlink()

    # First remains cached because it was touched.
    assert source.get_elevation(
        39.5,
        -84.5,
    ) == pytest.approx(
        100.0 * METERS_TO_FEET
    )

    # Second was least recently used and should
    # have been evicted.
    assert source.get_elevation(
        39.5,
        -83.5,
    ) is None

    # Third remains cached.
    assert source.get_elevation(
        39.5,
        -82.5,
    ) == pytest.approx(
        300.0 * METERS_TO_FEET
    )


@pytest.mark.parametrize(
    "cache_size",
    (
        0,
        -1,
        True,
        False,
        2.0,
        "2",
        None,
    ),
)
def test_cache_size_rejects_invalid_values(
    tmp_path: Path,
    cache_size,
) -> None:
    with pytest.raises(ValueError):
        SrtmTerrainSource(
            tmp_path,
            cache_size=cache_size,
        )


def test_cache_size_accepts_positive_integer(
    tmp_path: Path,
) -> None:
    source = SrtmTerrainSource(
        tmp_path,
        cache_size=2,
    )

    assert source.cache_size == 2
