from pathlib import Path

import yaml

from pyefis.user.blake_pfd.config_loader import (
    load_config,
)
from pyefis.user.blake_pfd.core.guidance_settings_store import (
    save_guidance_touch_settings,
)
from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
)


def test_saves_all_touch_settings(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "pfd_config.yaml"
    )

    config_path.write_text(
        """
guidance:
  hits_enabled: true
  flight_director_enabled: true

features:
  show_synthetic_vision: false
  show_flight_path_marker: true
""",
        encoding="utf-8",
    )

    save_guidance_touch_settings(
        GuidanceTouchSettings(
            hits_enabled=False,
            flight_director_enabled=False,
            flight_path_marker_enabled=False,
            synthetic_vision_enabled=True,
        ),
        path=config_path,
    )

    raw = yaml.safe_load(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        raw["guidance"]["hits_enabled"]
        is False
    )

    assert (
        raw["guidance"]
        ["flight_director_enabled"]
        is False
    )

    assert (
        raw["features"]
        ["show_flight_path_marker"]
        is False
    )

    assert (
        raw["features"]
        ["show_synthetic_vision"]
        is True
    )


def test_preserves_unrelated_config(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "pfd_config.yaml"
    )

    config_path.write_text(
        """
display:
  width: 1024
  height: 600

navigation:
  selected_waypoint_id: KHAO

guidance:
  hits_enabled: true
""",
        encoding="utf-8",
    )

    save_guidance_touch_settings(
        GuidanceTouchSettings(
            hits_enabled=False,
        ),
        path=config_path,
    )

    raw = yaml.safe_load(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        raw["display"]["width"]
        == 1024
    )

    assert (
        raw["display"]["height"]
        == 600
    )

    assert (
        raw["navigation"]
        ["selected_waypoint_id"]
        == "KHAO"
    )


def test_creates_missing_sections(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "pfd_config.yaml"
    )

    config_path.write_text(
        """
display:
  width: 1024
""",
        encoding="utf-8",
    )

    save_guidance_touch_settings(
        GuidanceTouchSettings(
            hits_enabled=False,
            flight_director_enabled=True,
            flight_path_marker_enabled=False,
            synthetic_vision_enabled=True,
        ),
        path=config_path,
    )

    raw = yaml.safe_load(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    assert "guidance" in raw
    assert "features" in raw


def test_saved_values_reload_through_config_loader(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "pfd_config.yaml"
    )

    save_guidance_touch_settings(
        GuidanceTouchSettings(
            hits_enabled=False,
            flight_director_enabled=False,
            flight_path_marker_enabled=False,
            synthetic_vision_enabled=True,
        ),
        path=config_path,
    )

    config = load_config(
        config_path
    )

    assert (
        config.guidance.hits_enabled
        is False
    )

    assert (
        config.guidance
        .flight_director_enabled
        is False
    )

    assert (
        config.features
        .show_flight_path_marker
        is False
    )

    assert (
        config.features
        .show_synthetic_vision
        is True
    )