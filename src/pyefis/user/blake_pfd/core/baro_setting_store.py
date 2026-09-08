from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from pyefis.user.blake_pfd.core.baro_setting_controller import (
    BaroSettingController,
)


STATE_VERSION = 1


class BaroSettingStore:
    """
    Persistent pilot BARO state.

    This store is intentionally separate from aircraft
    configuration. Invalid, corrupt, missing, or unknown
    persisted state falls back to the supplied configured
    default.
    """

    def __init__(
        self,
        path: str | Path,
    ) -> None:
        self.path = Path(path)

    @staticmethod
    def _validated_setting(
        value,
    ) -> float | None:
        try:
            controller = BaroSettingController(
                initial_inhg=float(value),
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return controller.setting_inhg

    def load(
        self,
        *,
        default_inhg: float,
    ) -> float:
        default_value = self._validated_setting(
            default_inhg
        )

        if default_value is None:
            raise ValueError(
                "default BARO setting must be valid"
            )

        if not self.path.exists():
            return default_value

        try:
            raw = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
            UnicodeError,
        ):
            return default_value

        if not isinstance(raw, dict):
            return default_value

        if raw.get("version") != STATE_VERSION:
            return default_value

        persisted_value = self._validated_setting(
            raw.get("baro_setting_inhg")
        )

        if persisted_value is None:
            return default_value

        return persisted_value

    def save(
        self,
        value_inhg,
    ) -> None:
        validated_value = self._validated_setting(
            value_inhg
        )

        if validated_value is None:
            raise ValueError(
                "BARO setting must be finite, within "
                "27.50-31.50 inHg, and expressed to "
                "hundredths"
            )

        payload = {
            "version": STATE_VERSION,
            "baro_setting_inhg": validated_value,
        }

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                json.dump(
                    payload,
                    temporary_file,
                    indent=2,
                    sort_keys=True,
                )

                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(
                    temporary_file.fileno()
                )

                temporary_path = Path(
                    temporary_file.name
                )

            temporary_path.replace(
                self.path
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()
