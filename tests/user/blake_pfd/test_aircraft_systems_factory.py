from pathlib import Path

import pytest

from pyefis.user.blake_pfd.config_loader import (
    load_config,
)
from pyefis.user.blake_pfd.core.aircraft_systems_factory import (
    build_aircraft_systems,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    NearbyAirportRecord,
)


def test_factory_shares_performance_configuration(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "pfd_config.yaml"

    config_path.write_text(
        """
performance:
  best_glide_speed_kt: 96.0
  glide_ratio: 11.5
  glide_reserve_altitude_ft: 700.0
""".strip()
    )

    config = load_config(config_path)
    systems = build_aircraft_systems(config)

    assert (
        systems.performance_config
        is config.performance
    )

    assert (
        systems.aircraft_intelligence.performance_config
        is config.performance
    )

    assert (
        systems.emergency_airport_manager.performance_config
        is config.performance
    )

    assert (
        systems.reachable_airport_pipeline.performance_config
        is config.performance
    )


def test_factory_pipeline_uses_yaml_glide_values(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "pfd_config.yaml"

    config_path.write_text(
        """
performance:
  best_glide_speed_kt: 96.0
  glide_ratio: 11.5
  glide_reserve_altitude_ft: 700.0
""".strip()
    )

    config = load_config(config_path)
    systems = build_aircraft_systems(config)

    result = systems.reachable_airport_pipeline.evaluate(
        airports=[
            NearbyAirportRecord(
                identifier="TEST",
                distance_nm=5.0,
                bearing_deg=0.0,
                elevation_ft=500.0,
            )
        ],
        aircraft_altitude_ft=6000.0,
    )

    expected_range_nm = (
        (6000.0 - 700.0)
        * 11.5
        / 6076.12
    )

    assert result.valid is True

    assert result.glide_range_nm == pytest.approx(
        expected_range_nm
    )


def test_factory_intelligence_uses_yaml_glide_speed(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "pfd_config.yaml"

    config_path.write_text(
        """
performance:
  best_glide_speed_kt: 100.0
  glide_ratio: 10.0
  glide_reserve_altitude_ft: 500.0
""".strip()
    )

    config = load_config(config_path)
    systems = build_aircraft_systems(config)

    assert (
        systems.aircraft_intelligence
        .performance_config
        .best_glide_speed_kt
        == 100.0
    )