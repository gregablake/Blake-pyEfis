from __future__ import annotations

from pathlib import Path


class ShutdownMarker:
    def __init__(
        self,
        path: str | Path,
    ) -> None:
        self.path = Path(path)

    def previous_shutdown_clean(
        self,
    ) -> bool:
        if not self.path.exists():
            return True

        try:
            value = (
                self.path
                .read_text(
                    encoding="utf-8"
                )
                .strip()
                .upper()
            )
        except OSError:
            return False

        return value == "CLEAN"

    def mark_running(
        self,
    ) -> None:
        self._write(
            "RUNNING"
        )

    def mark_clean_shutdown(
        self,
    ) -> None:
        self._write(
            "CLEAN"
        )

    def _write(
        self,
        value: str,
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = (
            self.path.with_suffix(
                self.path.suffix + ".tmp"
            )
        )

        temp_path.write_text(
            value,
            encoding="utf-8",
        )

        temp_path.replace(
            self.path
        )