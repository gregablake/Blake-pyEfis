from __future__ import annotations

import csv
from pathlib import Path
from time import monotonic

from pyefis.user.blake_pfd.flight_computer import FlightData


class LogReplaySource:
    def __init__(self, log_path: str | Path, replay_hz: float = 10.0) -> None:
        self.log_path = Path(log_path)
        self.replay_interval_s = 1.0 / replay_hz
        self.last_update_s = 0.0
        self.rows = self.load_rows()
        self.index = 0

    def load_rows(self) -> list[dict]:
        with self.log_path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def read(self) -> FlightData:
        now_s = monotonic()

        if now_s - self.last_update_s >= self.replay_interval_s:
            self.last_update_s = now_s
            self.index = min(self.index + 1, len(self.rows) - 1)

        row = self.rows[self.index]

        return FlightData(
            ias_kt=float(row.get("ias_kt", 0.0)),
            tas_kt=float(row.get("tas_kt", 0.0)),
            pressure_alt_ft=float(row.get("pressure_alt_ft", 0.0)),
            density_alt_ft=float(row.get("density_alt_ft", 0.0)),
            vsi_fpm=float(row.get("vsi_fpm", 0.0)),
            heading_deg=float(row.get("heading_deg", 0.0)),
            track_deg=float(row.get("track_deg", 0.0)),
            ground_speed_kt=float(row.get("ground_speed_kt", 0.0)),
            wind_speed_kt=float(row.get("wind_speed_kt", 0.0)),
            wind_direction_deg=float(row.get("wind_direction_deg", 0.0)),
            turn_rate_deg_sec=float(row.get("turn_rate_deg_sec", 0.0)),
            slip_skid=float(row.get("slip_skid", 0.0)),
            bearing_deg=float(row.get("bearing_deg", 0.0)),
            desired_track_deg=float(row.get("desired_track_deg", 0.0)),
            cdi=float(row.get("cdi", 0.0)),
            vdi=float(row.get("vdi", 0.0)),
            distance_to_waypoint_nm=float(row.get("distance_to_waypoint_nm", 0.0)),
            course_error_deg=float(row.get("course_error_deg", 0.0)),
            glidepath_target_alt_ft=float(row.get("glidepath_target_alt_ft", 0.0)),
            glidepath_alt_error_ft=float(row.get("glidepath_alt_error_ft", 0.0)),
        )