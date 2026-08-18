from __future__ import annotations

from pathlib import Path


class HeartbeatFile:
    def __init__(
        self,
        path: str | Path,
        write_interval_s: float = 0.5,
    ) -> None:
        self.path = Path(path)

        self.write_interval_s = max(
            0.1,
            float(write_interval_s),
        )

        self.last_write_s: float | None = None

    def maybe_write(
        self,
        timestamp_s: float,
    ) -> bool:
        now_s = float(timestamp_s)

        if (
            self.last_write_s is not None
            and (
                now_s
                - self.last_write_s
            )
            < self.write_interval_s
        ):
            return False

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        temp_path.write_text(
            f"{now_s:.6f}",
            encoding="utf-8",
        )

        temp_path.replace(
            self.path
        )

        self.last_write_s = now_s

        return True

    def remove(
        self,
    ) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass