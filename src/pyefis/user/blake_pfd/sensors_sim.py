"""
Blake PFD simulated sensor source.

This creates fake live-changing aircraft data so we can test the PFD brain
without real BNO085, BMP388, MPXV7002DP, GPS, or Stratux connected yet.
"""

from __future__ import annotations

from math import radians, sin, cos
from time import monotonic, sleep

from pyefis.user.blake_pfd.airdata import AirDataComputer, RawSensorInputs


class SimulatedSensorSource:
    """
    Generates fake aircraft sensor values.

    Later, this class gets replaced by real hardware readers:
    - BNO085 reader
    - BMP388 reader
    - MPXV7002DP/ADS1115 reader
    - GPS reader
    - Stratux GDL90 reader
    """

    def __init__(self) -> None:
        self.start_time_s = monotonic()

    def read(self) -> RawSensorInputs:
        """
        Return one simulated sensor packet.
        """

        t = monotonic() - self.start_time_s

        # Simulated attitude.
        pitch_deg = 3.0 * sin(t * 0.45)
        roll_deg = 20.0 * sin(t * 0.25)

        # Simulated heading slowly turning.
        heading_deg = (270.0 + (t * 2.0)) % 360.0

        # Simulated yaw/turn rate.
        yaw_rate_deg_s = 2.8 * sin(t * 0.35)

        # Simulated slip/skid.
        accel_y_g = 0.12 * sin(t * 0.7)
        accel_z_g = 1.0

        # Simulated pitot differential pressure.
        # Roughly cycles around cruise-speed-ish values.
        differential_pressure_pa = 850.0 + (250.0 * sin(t * 0.18))

        # Simulated static pressure.
        # Lower pressure = higher altitude.
        static_pressure_pa = 101325.0 - 1800.0 - (500.0 * sin(t * 0.12))

        # Simulated OAT.
        outside_air_temp_c = 18.0 + (2.0 * sin(t * 0.05))

        # Simulated GPS data.
        gps_track_deg = (heading_deg + 3.0 * sin(t * 0.22)) % 360.0
        gps_ground_speed_kt = 115.0 + (8.0 * sin(t * 0.2))

        # Simulated waypoint/nav info.
        waypoint_bearing_deg = 290.0
        desired_track_deg = 285.0
        cdi_deflection_nm = 0.75 * sin(t * 0.16)
        vdi_deflection_deg = 0.8 * sin(t * 0.12)

        return RawSensorInputs(
            differential_pressure_pa=differential_pressure_pa,
            static_pressure_pa=static_pressure_pa,
            outside_air_temp_c=outside_air_temp_c,
            pitch_deg=pitch_deg,
            roll_deg=roll_deg,
            yaw_rate_deg_s=yaw_rate_deg_s,
            accel_x_g=0.0,
            accel_y_g=accel_y_g,
            accel_z_g=accel_z_g,
            heading_deg=heading_deg,
            gps_track_deg=gps_track_deg,
            gps_ground_speed_kt=gps_ground_speed_kt,
            waypoint_bearing_deg=waypoint_bearing_deg,
            desired_track_deg=desired_track_deg,
            cdi_deflection_nm=cdi_deflection_nm,
            vdi_deflection_deg=vdi_deflection_deg,
        )


def print_pfd_line() -> None:
    """
    Demo loop that prints changing PFD values.
    Press Ctrl+C to stop.
    """

    sensors = SimulatedSensorSource()
    airdata = AirDataComputer()

    print("Blake PFD sensor simulator started.")
    print("Press Ctrl+C to stop.")
    print()

    while True:
        raw = sensors.read()
        pfd = airdata.update(raw)

        line = (
            f"IAS {pfd.indicated_airspeed_kt:5.1f} kt | "
            f"TAS {pfd.true_airspeed_kt:5.1f} kt | "
            f"ALT {pfd.altitude_ft:6.0f} ft | "
            f"VSI {pfd.vertical_speed_fpm:7.0f} fpm | "
            f"P {pfd.pitch_deg:5.1f} | "
            f"R {pfd.roll_deg:5.1f} | "
            f"HDG {pfd.heading_deg:6.1f} | "
            f"GS {pfd.ground_speed_kt:5.1f} | "
            f"TRN {pfd.turn_rate_deg_s:5.2f} | "
            f"BALL {pfd.slip_skid:5.2f} | "
            f"CDI {pfd.cdi_deflection_nm:5.2f} | "
            f"VDI {pfd.vdi_deflection_deg:5.2f}"
        )

        print(line)
        sleep(0.25)


if __name__ == "__main__":
    print_pfd_line()
