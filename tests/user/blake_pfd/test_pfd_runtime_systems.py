from pathlib import Path

from pyefis.user.blake_pfd.config_loader import (
    load_config,
)
from pyefis.user.blake_pfd.core.aircraft_systems_factory import (
    build_aircraft_systems,
)


def test_runtime_systems_share_loaded_performance_config(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "pfd_config.yaml"

    config_path.write_text(
        """
performance:
  best_glide_speed_kt: 97.0
  glide_ratio: 10.8
  glide_reserve_altitude_ft: 800.0
""".strip()
    )

    config = load_config(config_path)
    systems = build_aircraft_systems(config)

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

    assert (
        systems.aircraft_intelligence
        .performance_config
        .best_glide_speed_kt
        == 97.0
    )