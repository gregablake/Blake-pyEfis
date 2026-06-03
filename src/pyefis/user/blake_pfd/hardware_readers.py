"""
Blake PFD real hardware reader layer.

This file is the bridge between real sensors and the PFD data computer.

Planned hardware:
- BNO085 AHRS/IMU for pitch, roll, heading, yaw rate, accel
- BMP388/MS5611 baro sensor for static pressure / altitude
- MPXV7002DP differential pressure sensor through ADS1115 ADC
- GPS source for ground speed / track / navigation
- Stratux later for traffic/weather

This first version is intentionally safe:
- It can run without sensors connected.
- It returns fallback values instead of crashing.
- Later we replace each placeholder reader with real hardware code.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, asin, degrees
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

        Output:
        - pitch_deg
        - roll_deg
        - heading_deg
        - yaw_rate_deg_s
        - accel_x_g
        - accel_y_g
        - accel_z_g
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
            gyro_x, gyro_y, gyro_z = self.sensor.gyro

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
            self.last_update_s = now_s

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

    Static pressure should come from the aircraft static system.
    OAT may later come from a separate probe.
    """

    def __init__(self) -> None:
        self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return barometric/static data.

        Placeholder values for now.
        """

        return {
            "static_pressure_pa": 101325.0,
            "outside_air_temp_c": 15.0,
        }


class AirspeedReader:
    """
    Reads MPXV7002DP differential pressure through ADS1115.

    The MPXV7002DP sensor output is analog.
    ADS1115 converts that voltage to digital for Raspberry Pi.
    """

    def __init__(self) -> None:
        self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return differential pressure in Pascals.

        Placeholder value for now.
        """

        return {
            "differential_pressure_pa": 0.0,
        }


class GpsReader:
    """
    Reads GPS track, ground speed, bearing, and nav guidance.

    Later this can read from:
    - USB GPS through gpsd
    - Stratux
    - serial NMEA
    - custom waypoint database
    """

    def __init__(self) -> None:
        self.ok = False

    def read(self) -> dict[str, float]:
        """
        Return GPS/nav data.

        Placeholder values for now.
        """

        return {
            "gps_track_deg": 0.0,
            "gps_ground_speed_kt": 0.0,
            "waypoint_bearing_deg": 0.0,
            "desired_track_deg": 0.0,
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

    # Roll, x-axis rotation
    sinr_cosp = 2.0 * ((w * x) + (y * z))
    cosr_cosp = 1.0 - (2.0 * ((x * x) + (y * y)))
    roll = atan2(sinr_cosp, cosr_cosp)

    # Pitch, y-axis rotation
    sinp = 2.0 * ((w * y) - (z * x))
    if abs(sinp) >= 1.0:
        pitch = 1.57079632679 if sinp > 0 else -1.57079632679
    else:
        pitch = asin(sinp)

    # Yaw, z-axis rotation
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

if __name__ == "__main__":
    demo()