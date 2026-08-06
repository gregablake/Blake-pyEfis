from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees


@dataclass(frozen=True)
class FlightPathMarkerState:
    valid: bool = False
    x_offset_deg: float = 0.0
    y_offset_deg: float = 0.0
    flight_path_angle_deg: float = 0.0


class FlightPathMarker:

    def calculate(
        self,
        *,
        track_deg: float,
        heading_deg: float,
        ground_speed_kt: float,
        vertical_speed_fpm: float,
    ) -> FlightPathMarkerState:

        if ground_speed_kt < 20:
            return FlightPathMarkerState()

        x_offset = (
            (track_deg - heading_deg + 180.0)
            % 360.0
        ) - 180.0

        flight_path_angle = degrees(
            atan2(
                vertical_speed_fpm,
                ground_speed_kt * 101.27,
            )
        )

        return FlightPathMarkerState(
            valid=True,
            x_offset_deg=x_offset,
            y_offset_deg=-flight_path_angle,
            flight_path_angle_deg=flight_path_angle,
        )