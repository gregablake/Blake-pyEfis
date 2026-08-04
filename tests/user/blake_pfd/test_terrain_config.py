from pathlib import Path

from pyefis.user.blake_pfd.config_loader import (
    load_config,
)


def test_default_terrain_config(
    tmp_path: Path,
) -> None:
    missing_path = (
        tmp_path
        / "missing_config.yaml"
    )

    config = load_config(
        missing_path
    )

    assert config.terrain.source == "fallback"
    assert config.terrain.srtm_directory == ""
    assert config.terrain.sample_distances_nm == (
        1.0,
        2.0,
        3.0,
        5.0,
        8.0,
        10.0,
    )


def test_loads_srtm_terrain_config(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "terrain_config.yaml"
    )

    config_path.write_text(
        """
terrain:
  source: srtm
  srtm_directory: /opt/blake-efis/terrain
  sample_distances_nm:
    - 0.5
    - 1.0
    - 2.5
"""
    )

    config = load_config(
        config_path
    )

    assert config.terrain.source == "srtm"
    assert (
        config.terrain.srtm_directory
        == "/opt/blake-efis/terrain"
    )
    assert config.terrain.sample_distances_nm == [
        0.5,
        1.0,
        2.5,
    ]


def test_other_config_sections_still_use_defaults(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "terrain_only.yaml"
    )

    config_path.write_text(
        """
terrain:
  source: fallback
"""
    )

    config = load_config(
        config_path
    )

    assert config.display.width == 1024
    assert (
        config.navigation.selected_waypoint_id
        == "KHAO"
    )
    assert (
        config.performance.best_glide_speed_kt
        == 80.0
    )