from pathlib import Path

from pyefis.user.blake_pfd.config_loader import (
    load_config,
)


def test_default_guidance_config(
    tmp_path: Path,
) -> None:
    config = load_config(
        tmp_path / "missing.yaml"
    )

    assert config.guidance.hits_enabled is True
    assert (
        config.guidance.flight_director_enabled
        is True
    )


def test_loads_disabled_guidance_config(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "guidance.yaml"
    )

    config_path.write_text(
        """
guidance:
  hits_enabled: false
  flight_director_enabled: false
"""
    )

    config = load_config(
        config_path
    )

    assert config.guidance.hits_enabled is False
    assert (
        config.guidance.flight_director_enabled
        is False
    )


def test_partial_guidance_config_uses_defaults(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "guidance_partial.yaml"
    )

    config_path.write_text(
        """
guidance:
  hits_enabled: false
"""
    )

    config = load_config(
        config_path
    )

    assert config.guidance.hits_enabled is False
    assert (
        config.guidance.flight_director_enabled
        is True
    )