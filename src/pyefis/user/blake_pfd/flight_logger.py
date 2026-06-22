from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic


LOG_DIR = Path(__file__).parent / "logs"


class FlightLogger:
    def __init__(self, log_interval_s: float = 1.0) -> None:
        self.log_interval_s = log_interval_s
        self.last_log_time_s = 0.0
        self.path: Path | None = None
        self.fieldnames: list[str] | None = None

        LOG_DIR.mkdir(exist_ok=True)

    def maybe_log(self, pfd, waypoint_id: str, engine=None) -> None:
        now_s = monotonic()

        if now_s - self.last_log_time_s < self.log_interval_s:
            return

        self.last_log_time_s = now_s

        row = asdict(pfd)
        row["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        row["waypoint_id"] = waypoint_id
        if engine is not None:
            engine_row = asdict(engine)

            for key, value in engine_row.items():
                row[f"engine_{key}"] = value

        self.write_row(row)

    def write_row(self, row: dict) -> None:
        if self.path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self.path = LOG_DIR / f"flight_log_{timestamp}.csv"

        if self.fieldnames is None:
            self.fieldnames = list(row.keys())

        file_exists = self.path.exists()

        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)