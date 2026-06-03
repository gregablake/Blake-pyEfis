from dataclasses import dataclass


@dataclass
class FlightData:
    ias_kt: float = 0.0
    tas_kt: float = 0.0

    pressure_alt_ft: float = 0.0
    density_alt_ft: float = 0.0

    vsi_fpm: float = 0.0

    heading_deg: float = 0.0
    track_deg: float = 0.0

    ground_speed_kt: float = 0.0

    wind_speed_kt: float = 0.0
    wind_direction_deg: float = 0.0

    turn_rate_deg_sec: float = 0.0
    slip_skid: float = 0.0

class FlightComputer:

    def __init__(self):
        pass

    def update(self, raw):

        flight = FlightData()

        flight.heading_deg = raw.heading_deg
        flight.track_deg = raw.gps_track_deg

        flight.ground_speed_kt = raw.gps_ground_speed_kt

        flight.turn_rate_deg_sec = raw.yaw_rate_deg_s

        flight.bearing_deg = raw.waypoint_bearing_deg

        flight.desired_track_deg = raw.desired_track_deg

        flight.cdi = raw.cdi_deflection_nm

        flight.vdi = raw.vdi_deflection_deg

        return flight

    bearing_deg: float = 0.0
    desired_track_deg: float = 0.0

    cdi: float = 0.0
    vdi: float = 0.0