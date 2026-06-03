"""
Blake PFD airdata calculation module.

This file does not talk directly to hardware yet.
It takes sensor-style inputs and converts them into values useful for a PFD.

Later inputs will come from:
- BNO085 AHRS
- MPXV7002DP airspeed sensor
- BMP388 / MS5611 baro sensor
- GPS / Stratux
- Arduino engine serial data
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees, radians, sin, cos, sqrt
from time import monotonic


KNOTS_PER_MPS = 1.943844
FT_PER_METER = 3.28084
PA_STANDARD_SEA_LEVEL = 101325.0
TEMP_STANDARD_K = 288.15
LAPSE_RATE = 0.0065
GAS_CONSTANT_AIR = 287.05
GRAVITY = 9.80665


@dataclass
class RawSensorInputs:
    """
    Raw sensor values coming from hardware or simulator.
    """

    differential_pressure_pa: float = 0.0
    static_pressure_pa: float = PA_STANDARD_SEA_LEVEL
    outside_air_temp_c: float = 15.0

    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    yaw_rate_deg_s: float = 0.0

    accel_x_g: float = 0.0
    accel_y_g: float = 0.0
    accel_z_g: float = 1.0

    heading_deg: float = 0.0
    gps_track_deg: float = 0.0
    gps_ground_speed_kt: float = 0.0

    waypoint_bearing_deg: float = 0.0
    desired_track_deg: float = 0.0
    cdi_deflection_nm: float = 0.0
    vdi_deflection_deg: float = 0.0


@dataclass
class PfdData:
    """
    Clean values ready for display on the PFD.
    """

    indicated_airspeed_kt: float
    true_airspeed_kt: float
    altitude_ft: float
    vertical_speed_fpm: float

    outside_air_temp_c: float

    pitch_deg: float
    roll_deg: float
    heading_deg: float
    gps_track_deg: float
    ground_speed_kt: float

    turn_rate_deg_s: float
    standard_rate_ratio: float
    slip_skid: float

    wind_speed_kt: float
    wind_direction_deg: float

    waypoint_bearing_deg: float
    desired_track_deg: float
    cdi_deflection_nm: float
    vdi_deflection_deg: float


class AirDataComputer:
    """
    Converts raw sensor values into display-ready PFD values.
    """

    def __init__(self) -> None:
        self._last_altitude_ft: float | None = None
        self._last_time_s: float | None = None
        self._vertical_speed_fpm: float = 0.0

    def update(self, raw: RawSensorInputs) -> PfdData:
        altitude_ft = pressure_to_altitude_ft(raw.static_pressure_pa)

        now_s = monotonic()
        self._vertical_speed_fpm = self._calculate_vsi(altitude_ft, now_s)

        ias_kt = differential_pressure_to_ias_kt(raw.differential_pressure_pa)
        tas_kt = estimate_true_airspeed_kt(
            indicated_airspeed_kt=ias_kt,
            altitude_ft=altitude_ft,
            outside_air_temp_c=raw.outside_air_temp_c,
        )

        standard_rate_ratio = raw.yaw_rate_deg_s / 3.0

        slip_skid = calculate_slip_skid(
            accel_y_g=raw.accel_y_g,
            accel_z_g=raw.accel_z_g,
        )

        wind_speed_kt, wind_direction_deg = estimate_wind(
            true_airspeed_kt=tas_kt,
            heading_deg=raw.heading_deg,
            ground_speed_kt=raw.gps_ground_speed_kt,
            track_deg=raw.gps_track_deg,
        )

        return PfdData(
            indicated_airspeed_kt=ias_kt,
            true_airspeed_kt=tas_kt,
            altitude_ft=altitude_ft,
            vertical_speed_fpm=self._vertical_speed_fpm,
            outside_air_temp_c=raw.outside_air_temp_c,
            pitch_deg=raw.pitch_deg,
            roll_deg=raw.roll_deg,
            heading_deg=normalize_degrees(raw.heading_deg),
            gps_track_deg=normalize_degrees(raw.gps_track_deg),
            ground_speed_kt=raw.gps_ground_speed_kt,
            turn_rate_deg_s=raw.yaw_rate_deg_s,
            standard_rate_ratio=standard_rate_ratio,
            slip_skid=slip_skid,
            wind_speed_kt=wind_speed_kt,
            wind_direction_deg=wind_direction_deg,
            waypoint_bearing_deg=normalize_degrees(raw.waypoint_bearing_deg),
            desired_track_deg=normalize_degrees(raw.desired_track_deg),
            cdi_deflection_nm=raw.cdi_deflection_nm,
            vdi_deflection_deg=raw.vdi_deflection_deg,
        )

    def _calculate_vsi(self, altitude_ft: float, now_s: float) -> float:
        if self._last_altitude_ft is None or self._last_time_s is None:
            self._last_altitude_ft = altitude_ft
            self._last_time_s = now_s
            return 0.0

        dt_s = now_s - self._last_time_s
        if dt_s <= 0.05:
            return self._vertical_speed_fpm

        raw_vsi_fpm = ((altitude_ft - self._last_altitude_ft) / dt_s) * 60.0

        # Simple smoothing so VSI does not jump around like a caffeinated squirrel.
        alpha = 0.15
        smoothed_vsi_fpm = (alpha * raw_vsi_fpm) + ((1.0 - alpha) * self._vertical_speed_fpm)

        self._last_altitude_ft = altitude_ft
        self._last_time_s = now_s

        return smoothed_vsi_fpm


def differential_pressure_to_ias_kt(differential_pressure_pa: float) -> float:
    """
    Convert pitot-static differential pressure to indicated airspeed.

    q = dynamic pressure in Pascals.
    IAS m/s = sqrt(2q / sea-level air density)
    """

    q_pa = max(differential_pressure_pa, 0.0)
    rho_sea_level = 1.225

    airspeed_mps = sqrt((2.0 * q_pa) / rho_sea_level)
    return airspeed_mps * KNOTS_PER_MPS


def pressure_to_altitude_ft(static_pressure_pa: float) -> float:
    """
    Convert static pressure to pressure altitude in feet.
    """

    pressure = max(static_pressure_pa, 1.0)

    altitude_m = (TEMP_STANDARD_K / LAPSE_RATE) * (
        1.0 - (pressure / PA_STANDARD_SEA_LEVEL) ** (
            (GAS_CONSTANT_AIR * LAPSE_RATE) / GRAVITY
        )
    )

    return altitude_m * FT_PER_METER


def estimate_true_airspeed_kt(
    indicated_airspeed_kt: float,
    altitude_ft: float,
    outside_air_temp_c: float,
) -> float:
    """
    Simple TAS estimate.

    This is good enough for development display.
    Later we can improve this using full density altitude calculations.
    """

    altitude_correction = 1.0 + (0.02 * (altitude_ft / 1000.0))
    temp_correction = 1.0 + ((outside_air_temp_c - 15.0) * 0.001)

    return indicated_airspeed_kt * altitude_correction * temp_correction


def calculate_slip_skid(accel_y_g: float, accel_z_g: float) -> float:
    """
    Estimate slip/skid ball position from lateral acceleration.

    Negative = ball left
    Positive = ball right

    Output is limited to roughly -1.0 to +1.0 for display.
    """

    if abs(accel_z_g) < 0.05:
        return 0.0

    slip = accel_y_g / abs(accel_z_g)

    return clamp(slip, -1.0, 1.0)


def estimate_wind(
    true_airspeed_kt: float,
    heading_deg: float,
    ground_speed_kt: float,
    track_deg: float,
) -> tuple[float, float]:
    """
    Estimate wind vector from aircraft air vector and GPS ground vector.

    This is a simplified wind estimate.
    Requires decent heading source and GPS track.
    """

    heading_rad = radians(heading_deg)
    track_rad = radians(track_deg)

    air_north = true_airspeed_kt * cos(heading_rad)
    air_east = true_airspeed_kt * sin(heading_rad)

    ground_north = ground_speed_kt * cos(track_rad)
    ground_east = ground_speed_kt * sin(track_rad)

    wind_north = ground_north - air_north
    wind_east = ground_east - air_east

    wind_speed = sqrt((wind_north ** 2) + (wind_east ** 2))

    # Direction wind is coming FROM.
    wind_to_deg = degrees(atan2(wind_east, wind_north))
    wind_from_deg = normalize_degrees(wind_to_deg + 180.0)

    return wind_speed, wind_from_deg


def normalize_degrees(value: float) -> float:
    return value % 360.0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def demo() -> None:
    """
    Demo data so we can test the file without real sensors connected.
    """

    computer = AirDataComputer()

    raw = RawSensorInputs(
        differential_pressure_pa=900.0,
        static_pressure_pa=100500.0,
        outside_air_temp_c=18.0,
        pitch_deg=2.5,
        roll_deg=8.0,
        yaw_rate_deg_s=2.8,
        accel_y_g=0.08,
        accel_z_g=0.99,
        heading_deg=275.0,
        gps_track_deg=278.0,
        gps_ground_speed_kt=124.0,
        waypoint_bearing_deg=290.0,
        desired_track_deg=285.0,
        cdi_deflection_nm=-0.3,
        vdi_deflection_deg=0.4,
    )

    pfd = computer.update(raw)

    print("===== Blake PFD Demo Data =====")
    print(f"IAS: {pfd.indicated_airspeed_kt:.1f} kt")
    print(f"TAS: {pfd.true_airspeed_kt:.1f} kt")
    print(f"ALT: {pfd.altitude_ft:.0f} ft")
    print(f"VSI: {pfd.vertical_speed_fpm:.0f} fpm")
    print(f"OAT: {pfd.outside_air_temp_c:.1f} C")
    print(f"Pitch: {pfd.pitch_deg:.1f} deg")
    print(f"Roll: {pfd.roll_deg:.1f} deg")
    print(f"HDG: {pfd.heading_deg:.0f} deg")
    print(f"TRK: {pfd.gps_track_deg:.0f} deg")
    print(f"GS: {pfd.ground_speed_kt:.1f} kt")
    print(f"Turn Rate: {pfd.turn_rate_deg_s:.1f} deg/s")
    print(f"Std Rate Ratio: {pfd.standard_rate_ratio:.2f}")
    print(f"Slip/Skid: {pfd.slip_skid:.2f}")
    print(f"Wind: {pfd.wind_direction_deg:.0f} deg at {pfd.wind_speed_kt:.1f} kt")
    print(f"CDI: {pfd.cdi_deflection_nm:.2f} nm")
    print(f"VDI: {pfd.vdi_deflection_deg:.2f} deg")


if __name__ == "__main__":
    demo()
