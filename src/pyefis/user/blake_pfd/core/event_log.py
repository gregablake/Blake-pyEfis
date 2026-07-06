from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


class EventLog:
    def __init__(self, filename: str = "efis_events.csv") -> None:
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_path = self.log_dir / filename

    def write(self, event_type: str, message: str) -> None:
        file_exists = self.log_path.exists()

        with self.log_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["timestamp_utc", "event_type", "message"],
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "event_type": event_type,
                    "message": message,
                }
            )