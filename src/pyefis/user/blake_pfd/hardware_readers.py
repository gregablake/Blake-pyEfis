"""
Blake PFD real hardware reader layer.

This file is the bridge between real sensors and the PFD data computer.

Planned hardware:
- BNO085 AHRS/IMU for pitch, roll, heading, yaw rate, accel
- BMP388/MS5611 baro sensor for static pressure / altitude
- MPXV7002DP differential pressure sensor through ADS1115 ADC
- GPS source for ground speed / track / navigation
- Stratux later for traffic/weather

This version is intentionally safe:
- It can run without sensors connected.
- It returns fallback values instead of crashing.
- Later we replace/refine each reader with calibrated hardware code.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, cos, degrees, radians, sin
from time import monotonic

from pyefis.user.blake_pfd.airdata import RawSensorInputs


@dataclass
class HardwareStatus:
    """
    Tracks whether each hardware source is currently working.
    """

    bno085_ok: bool = False
    baro_ok: bool = False
    airspeed_ok: bool = False
    gps_ok: bool = False

    bno085_last_success_s: float | None = None
    baro_last_success_s: float | None = None
    airspeed_last_success_s: float | None = None
    gps_last_success_s: float | None = None

class Bno085Reader:
    """
    Reads attitude, heading, yaw rate, and acceleration from BNO085.

    This class is written so it can run in Codespaces without hardware.
    On the Raspberry Pi, install the Adafruit BNO08x library and wire the sensor.
    """

    def __init__(self) -> None:
        self.ok = False
        self.last_heading_deg = 0.0
        self.last_yaw_deg = 0.0
        self.last_update_s = monotonic()
        self.last_success_s: float | None = None
        self.sensor = None

        try:
            import board
            import busio
            from adafruit_bno08x import (
                BNO_REPORT_ACCELEROMETER,
                BNO_REPORT_GYROSCOPE,
                BNO_REPORT_ROTATION_VECTOR,
            )
            from adafruit_bno08x.i2c import BNO08X_I2C

            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = BNO08X_I2C(i2c)

            self.sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
            self.sensor.enable_feature(BNO_REPORT_GYROSCOPE)
            self.sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)

            self.ok = True

        except Exception as exc:
            print(f"BNO085 not active, using fallback values: {exc}")
            self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return AHRS-style data.
        """

        if not self.ok or self.sensor is None:
            return {
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "heading_deg": self.last_heading_deg,
                "yaw_rate_deg_s": 0.0,
                "accel_x_g": 0.0,
                "accel_y_g": 0.0,
                "accel_z_g": 1.0,
            }

        try:
            quat_i, quat_j, quat_k, quat_real = self.sensor.quaternion
            accel_x, accel_y, accel_z = self.sensor.acceleration

            roll_deg, pitch_deg, yaw_deg = quaternion_to_euler_deg(
                quat_i,
                quat_j,
                quat_k,
                quat_real,
            )

            now_s = monotonic()
            dt_s = now_s - self.last_update_s

            if dt_s > 0.02:
                yaw_rate_deg_s = angle_delta_deg(yaw_deg, self.last_yaw_deg) / dt_s
            else:
                yaw_rate_deg_s = 0.0

            self.last_yaw_deg = yaw_deg
            self.last_heading_deg = yaw_deg
            
            self.last_success_s = now_s

            # Convert m/s^2 to g.
            accel_x_g = accel_x / 9.80665
            accel_y_g = accel_y / 9.80665
            accel_z_g = accel_z / 9.80665

            return {
                "pitch_deg": pitch_deg,
                "roll_deg": roll_deg,
                "heading_deg": yaw_deg,
                "yaw_rate_deg_s": yaw_rate_deg_s,
                "accel_x_g": accel_x_g,
                "accel_y_g": accel_y_g,
                "accel_z_g": accel_z_g,
            }

        except Exception as exc:
            print(f"BNO085 read failed: {exc}")
            self.ok = False

            return {
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "heading_deg": self.last_heading_deg,
                "yaw_rate_deg_s": 0.0,
                "accel_x_g": 0.0,
                "accel_y_g": 0.0,
                "accel_z_g": 1.0,
            }


class BaroReader:
    """
    Reads static pressure and outside air temperature.

    Primary planned sensor:
    - BMP388 barometric pressure sensor

    Static pressure should ideally come from the aircraft static system,
    not loose cabin air, if you want EFIS altitude/VSI to agree with pitot/static.
    """

    def __init__(self) -> None:
        self.ok = False
        self.sensor = None
        self.last_success_s: float | None = None

        try:
            import board
            import busio
            import adafruit_bmp3xx

            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_bmp3xx.BMP3XX_I2C(i2c)

            # Sea-level pressure is used internally by the library if using
            # sensor.altitude, but our airdata computer uses raw pressure.
            self.sensor.sea_level_pressure = 1013.25

            self.ok = True

        except Exception as exc:
            print(f"BMP388 not active, using fallback values: {exc}")
            self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return static pressure in Pascals and OAT in Celsius.
        """

        if not self.ok or self.sensor is None:
            return {
                "static_pressure_pa": 101325.0,
                "outside_air_temp_c": 15.0,
            }

        try:
            # Adafruit BMP3XX pressure is in hPa.
            pressure_hpa = float(self.sensor.pressure)
            temperature_c = float(self.sensor.temperature)

            static_pressure_pa = pressure_hpa * 100.0
            self.last_success_s = monotonic()
            
            return {
                "static_pressure_pa": static_pressure_pa,
                "outside_air_temp_c": temperature_c,
            }

        except Exception as exc:
            print(f"BMP388 read failed: {exc}")
            self.ok = False

            return {
                "static_pressure_pa": 101325.0,
                "outside_air_temp_c": 15.0,
            }


class AirspeedReader:
    """
    Reads MPXV7002DP differential pressure through ADS1115.

    Hardware path:
        MPXV7002DP analog output -> ADS1115 A0 -> Raspberry Pi I2C

    MPXV7002DP basics:
    - 5V sensor supply recommended
    - Zero differential pressure output is about Vcc / 2
    - Sensitivity is roughly 1.0 V per kPa
    - Range is approximately -2 kPa to +2 kPa

    We only use positive pressure for airspeed:
        pitot pressure - static pressure
    """

    def __init__(self) -> None:
        self.ok = False
        self.ads = None
        self.channel = None
        self.last_success_s: float | None = None

        # Calibration values.
        # These can be adjusted later after real sensor testing.
        self.sensor_supply_v = 5.0
        self.zero_pressure_v = 2.5
        self.volts_per_kpa = 1.0

        try:
            import board
            import busio
            import adafruit_ads1x15.ads1115 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn

            i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(i2c)

            # ADS1115 input A0.
            self.channel = AnalogIn(self.ads, ADS.P0)

            self.ok = True

        except Exception as exc:
            print(f"ADS1115/MPXV7002DP not active, using fallback values: {exc}")
            self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return differential pressure in Pascals.
        """

        if not self.ok or self.channel is None:
            return {
                "differential_pressure_pa": 0.0,
            }

        try:
            voltage = float(self.channel.voltage)
            differential_pressure_pa = self.voltage_to_pressure_pa(voltage)
            self.last_success_s = monotonic()

            return {
                "differential_pressure_pa": differential_pressure_pa,
            }

        except Exception as exc:
            print(f"ADS1115/MPXV7002DP read failed: {exc}")
            self.ok = False

            return {
                "differential_pressure_pa": 0.0,
            }

    def voltage_to_pressure_pa(self, voltage: float) -> float:
        """
        Convert MPXV7002DP voltage to differential pressure.

        Approximation:
            pressure_kpa = (voltage - zero_voltage) / volts_per_kpa

        Then:
            pressure_pa = pressure_kpa * 1000

        Negative pressure is clamped to zero for IAS.
        """

        pressure_kpa = (voltage - self.zero_pressure_v) / self.volts_per_kpa
        pressure_pa = pressure_kpa * 1000.0

        return max(pressure_pa, 0.0)


class GpsReader:
    """
    Reads GPS track, ground speed, and basic navigation data.

    Planned sources:
    - gpsd from USB GPS
    - Stratux later
    - Custom waypoint database later

    This first version supports gpsd if available,
    but safely falls back when running in Codespaces.
    """

    def __init__(self) -> None:
        self.ok = False
        self.gps_session = None
        self.last_success_s: float | None = None
        self.last_track_deg = 0.0
        self.last_ground_speed_kt = 0.0

        # Temporary selected waypoint placeholder.
        # Later this will come from airport/navpoint entry.
        self.selected_waypoint_lat = 39.1031
        self.selected_waypoint_lon = -84.5120
        self.desired_track_deg = 0.0

        try:
            import gps

            self.gps_session = gps.gps(mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
            self.ok = True

        except Exception as exc:
            print(f"GPS/gpsd not active, using fallback values: {exc}")
            self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return GPS/nav data.
        """

        if not self.ok or self.gps_session is None:
            return self._fallback()

        try:
            report = self.gps_session.next()

            if report.get("class") != "TPV":
                return self._fallback()

            track_deg = float(getattr(report, "track", self.last_track_deg))
            speed_mps = float(getattr(report, "speed", 0.0))
            ground_speed_kt = speed_mps * 1.943844

            lat = getattr(report, "lat", None)
            lon = getattr(report, "lon", None)

            if lat is not None and lon is not None:
                waypoint_bearing_deg = bearing_between_points_deg(
                    float(lat),
                    float(lon),
                    self.selected_waypoint_lat,
                    self.selected_waypoint_lon,
                )
            else:
                waypoint_bearing_deg = 0.0

            self.last_track_deg = track_deg
            self.last_ground_speed_kt = ground_speed_kt
            self.last_success_s = monotonic()

            return {
                "gps_track_deg": track_deg % 360.0,
                "gps_ground_speed_kt": ground_speed_kt,
                "waypoint_bearing_deg": waypoint_bearing_deg,
                "desired_track_deg": self.desired_track_deg,
                "cdi_deflection_nm": 0.0,
                "vdi_deflection_deg": 0.0,
            }

        except Exception as exc:
            print(f"GPS/gpsd read failed: {exc}")
            self.ok = False
            return self._fallback()

    def _fallback(self) -> dict[str, float]:
        return {
            "gps_track_deg": self.last_track_deg,
            "gps_ground_speed_kt": self.last_ground_speed_kt,
            "waypoint_bearing_deg": 0.0,
            "desired_track_deg": self.desired_track_deg,
            "cdi_deflection_nm": 0.0,
            "vdi_deflection_deg": 0.0,
        }


class BlakeHardwareSensorSource:
    """
    Combines all hardware readers into one RawSensorInputs packet.
    """

    def __init__(self) -> None:
        self.bno085 = Bno085Reader()
        self.baro = BaroReader()
        self.airspeed = AirspeedReader()
        self.gps = GpsReader()
        self.status = HardwareStatus()

    def read(self) -> RawSensorInputs:
        """
        Read all available sensors and return one clean RawSensorInputs object.
        """

        bno = self.bno085.read()
        baro = self.baro.read()
        airspeed = self.airspeed.read()
        gps = self.gps.read()

        self.status.bno085_ok = self.bno085.ok
        self.status.baro_ok = self.baro.ok
        self.status.airspeed_ok = self.airspeed.ok
        self.status.gps_ok = self.gps.ok
        
        self.status.bno085_last_success_s = (
            self.bno085.last_success_s
        )

        self.status.baro_last_success_s = (
            self.baro.last_success_s
        )

        self.status.airspeed_last_success_s = (
            self.airspeed.last_success_s
        )

        self.status.gps_last_success_s = (
            self.gps.last_success_s
        )

        return RawSensorInputs(
            differential_pressure_pa=airspeed["differential_pressure_pa"],
            static_pressure_pa=baro["static_pressure_pa"],
            outside_air_temp_c=baro["outside_air_temp_c"],
            pitch_deg=bno["pitch_deg"],
            roll_deg=bno["roll_deg"],
            yaw_rate_deg_s=bno["yaw_rate_deg_s"],
            accel_x_g=bno["accel_x_g"],
            accel_y_g=bno["accel_y_g"],
            accel_z_g=bno["accel_z_g"],
            heading_deg=bno["heading_deg"],
            gps_track_deg=gps["gps_track_deg"],
            gps_ground_speed_kt=gps["gps_ground_speed_kt"],
            waypoint_bearing_deg=gps["waypoint_bearing_deg"],
            desired_track_deg=gps["desired_track_deg"],
            cdi_deflection_nm=gps["cdi_deflection_nm"],
            vdi_deflection_deg=gps["vdi_deflection_deg"],
        )


def quaternion_to_euler_deg(
    x: float,
    y: float,
    z: float,
    w: float,
) -> tuple[float, float, float]:
    """
    Convert quaternion to roll, pitch, yaw in degrees.

    Returns:
        roll_deg, pitch_deg, yaw_deg
    """

    # Roll, x-axis rotation.
    sinr_cosp = 2.0 * ((w * x) + (y * z))
    cosr_cosp = 1.0 - (2.0 * ((x * x) + (y * y)))
    roll = atan2(sinr_cosp, cosr_cosp)

    # Pitch, y-axis rotation.
    sinp = 2.0 * ((w * y) - (z * x))
    if abs(sinp) >= 1.0:
        pitch = 1.57079632679 if sinp > 0 else -1.57079632679
    else:
        pitch = asin(sinp)

    # Yaw, z-axis rotation.
    siny_cosp = 2.0 * ((w * z) + (x * y))
    cosy_cosp = 1.0 - (2.0 * ((y * y) + (z * z)))
    yaw = atan2(siny_cosp, cosy_cosp)

    roll_deg = degrees(roll)
    pitch_deg = degrees(pitch)
    yaw_deg = degrees(yaw) % 360.0

    return roll_deg, pitch_deg, yaw_deg


def angle_delta_deg(new_angle: float, old_angle: float) -> float:
    """
    Smallest signed angle difference between two headings.
    """

    return (new_angle - old_angle + 180.0) % 360.0 - 180.0


def bearing_between_points_deg(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float,
) -> float:
    """
    Calculate initial bearing from point 1 to point 2.
    """

    lat1 = radians(lat1_deg)
    lat2 = radians(lat2_deg)
    dlon = radians(lon2_deg - lon1_deg)

    x = sin(dlon) * cos(lat2)
    y = (cos(lat1) * sin(lat2)) - (sin(lat1) * cos(lat2) * cos(dlon))

    bearing = degrees(atan2(x, y))

    return bearing % 360.0


def demo() -> None:
    """
    Quick hardware reader smoke test.
    """

    source = BlakeHardwareSensorSource()
    raw = source.read()

    print("===== Blake Hardware Reader Demo =====")
    print(raw)
    print()
    print("Hardware status:")
    print(source.status)


if __name__ == "__main__":
    demo()
