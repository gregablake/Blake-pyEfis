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

    def maybe_log(
        self,
        pfd,
        waypoint_id: str,
        engine=None,
        sensor_status=None,
    ) -> None:
        now_s = monotonic()

        if now_s - self.last_log_time_s < self.log_interval_s:
            return

        self.last_log_time_s = now_s

        row = asdict(pfd)
        row["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        row["waypoint_id"] = waypoint_id
        
        engine_row = asdict(engine)

        for key, value in engine_row.items():
            if key == "cht_f":
                for idx, cht in enumerate(value, start=1):
                    row[f"engine_cht_{idx}"] = cht

            elif key == "egt_f":
                for idx, egt in enumerate(value, start=1):
                    row[f"engine_egt_{idx}"] = egt

            else:
                row[f"engine_{key}"] = value

        def add_status(
            prefix: str,
            status,
        ) -> None:
            if status is None:
                row[f"{prefix}_valid"] = ""
                row[f"{prefix}_fresh"] = ""
                return

            row[f"{prefix}_valid"] = bool(status.valid)
            row[f"{prefix}_fresh"] = bool(status.fresh)

        if sensor_status is None:
            scalar_statuses = {
                "engine_rpm": None,
                "engine_volts": None,
                "engine_amps": None,
                "engine_oil_pressure_psi": None,
                "engine_oil_temp_f": None,
                "engine_fuel_pressure_psi": None,
                "engine_fuel_flow_gph": None,
            }
        else:
            scalar_statuses = {
                "engine_rpm": sensor_status.rpm,
                "engine_volts": sensor_status.volts,
                "engine_amps": sensor_status.amps,
                "engine_oil_pressure_psi": sensor_status.oil_pressure,
                "engine_oil_temp_f": sensor_status.oil_temperature,
                "engine_fuel_pressure_psi": sensor_status.fuel_pressure,
                "engine_fuel_flow_gph": sensor_status.fuel_flow,
            }

        for prefix, status in scalar_statuses.items():
            add_status(
                prefix,
                status,
            )

        for index in range(6):
            status = None

            if (
                sensor_status is not None
                and index < len(sensor_status.cht)
            ):
                status = sensor_status.cht[index]

            add_status(
                f"engine_cht_{index + 1}",
                status,
            )

        for index in range(2):
            status = None

            if (
                sensor_status is not None
                and index < len(sensor_status.egt)
            ):
                status = sensor_status.egt[index]

            add_status(
                f"engine_egt_{index + 1}",
                status,
            )

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