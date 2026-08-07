from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml

from pyefis.user.blake_pfd.config_loader import (
    CONFIG_PATH,
)
from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
)


def save_guidance_touch_settings(
    settings: GuidanceTouchSettings,
    path: Path = CONFIG_PATH,
) -> None:
    """
    Persist touchscreen guidance selections while
    preserving unrelated PFD configuration.
    """

    config_path = Path(path)

    raw = _load_existing_config(
        config_path
    )

    guidance = _ensure_section(
        raw,
        "guidance",
    )

    features = _ensure_section(
        raw,
        "features",
    )

    guidance["hits_enabled"] = bool(
        settings.hits_enabled
    )

    guidance["flight_director_enabled"] = bool(
        settings.flight_director_enabled
    )

    features["show_flight_path_marker"] = bool(
        settings.flight_path_marker_enabled
    )

    features["show_synthetic_vision"] = bool(
        settings.synthetic_vision_enabled
    )

    _atomic_write_yaml(
        config_path,
        raw,
    )


def _load_existing_config(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        loaded = yaml.safe_load(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        yaml.YAMLError,
    ):
        return {}

    if not isinstance(
        loaded,
        dict,
    ):
        return {}

    return loaded


def _ensure_section(
    raw: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    section = raw.get(
        key
    )

    if isinstance(
        section,
        dict,
    ):
        return section

    section = {}

    raw[key] = section

    return section


def _atomic_write_yaml(
    path: Path,
    raw: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    yaml_text = yaml.safe_dump(
        raw,
        sort_keys=False,
        default_flow_style=False,
    )

    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(
                yaml_text
            )

            temporary_file.flush()

            temporary_path = Path(
                temporary_file.name
            )

        temporary_path.replace(
            path
        )

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()