from pathlib import Path

import pytest

from pyefis.user.blake_pfd.config_loader import (
    load_config,
)


def test_config_loader_uses_default_aircraft_performance(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "missing.yaml"

    config = load_config(
        config_path,
    )

    assert config.performance.best_glide_speed_kt == 80.0
    assert config.performance.glide_ratio == 9.0

    assert (
        config.performance.glide_reserve_altitude_ft
        == 1000.0
    )


def test_config_loader_reads_aircraft_performance(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "pfd_config.yaml"

    config_path.write_text(
        """
performance:
  best_glide_speed_kt: 92.0
  glide_ratio: 10.5
  glide_reserve_altitude_ft: 750.0
""".strip()
    )

    config = load_config(
        config_path,
    )

    assert config.performance.best_glide_speed_kt == 92.0
    assert config.performance.glide_ratio == 10.5

    assert (
        config.performance.glide_reserve_altitude_ft
        == 750.0
    )


def test_config_loader_rejects_invalid_performance(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "pfd_config.yaml"

    config_path.write_text(
        """
performance:
  best_glide_speed_kt: 0.0
""".strip()
    )

    with pytest.raises(
        ValueError,
        match="best_glide_speed_kt",
    ):
        load_config(
            config_path,
        )