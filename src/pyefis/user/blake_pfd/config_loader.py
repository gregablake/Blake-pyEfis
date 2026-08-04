"""
Blake PFD configuration loader.

Loads pfd_config.yaml and provides clean access to display settings,
sensor mode, feature toggles, waypoint data, and future database paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pyefis.user.blake_pfd.core.aircraft_performance_config import (
    AircraftPerformanceConfig,
)


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


@dataclass
class DisplayConfig:
    width: int = 1024
    height: int = 600
    fullscreen: bool = True
    ui_scale: float = 1.0


@dataclass
class SensorConfig:
    mode: str = "sim"


@dataclass
class FeatureConfig:
    show_nearest_airports: bool = True
    show_airspeed: bool = True
    show_altitude: bool = True
    show_attitude: bool = True
    show_heading: bool = True
    show_vsi: bool = True
    show_turn_rate: bool = True
    show_slip_skid: bool = True
    show_oat: bool = True
    show_tas: bool = True
    show_ground_speed: bool = True
    show_wind: bool = True
    show_cdi: bool = True
    show_vdi: bool = True
    show_hsi: bool = True
    show_synthetic_vision: bool = False
    show_terrain: bool = True
    show_highway_in_sky: bool = False
    show_safe_taxi: bool = False
    show_traffic: bool = False
    show_weather: bool = False
    show_obstacles: bool = True
    show_moving_map: bool = True
    show_airport_info: bool = True
    show_route: bool = True
    
@dataclass
class NavigationConfig:
    selected_waypoint_id: str = "KHAO"
    selected_waypoint_name: str = "Butler County Regional"
    selected_waypoint_lat: float = 39.3638
    selected_waypoint_lon: float = -84.5220
    desired_track_deg: float = 0.0


@dataclass
class AirspeedConfig:
    vso_kt: float = 45.0
    vs_kt: float = 50.0
    vx_kt: float = 75.0
    vy_kt: float = 85.0
    va_kt: float = 120.0
    vno_kt: float = 150.0
    vne_kt: float = 180.0


@dataclass
class AltitudeConfig:
    baro_setting_inhg: float = 29.92


@dataclass
class SyntheticVisionConfig:
    terrain_database_path: str = ""
    obstacle_database_path: str = ""
    airport_database_path: str = ""
    
@dataclass
class TerrainConfig:
    source: str = "fallback"
    srtm_directory: str = ""
    sample_distances_nm: tuple[
        float,
        ...,
    ] = (
        1.0,
        2.0,
        3.0,
        5.0,
        8.0,
        10.0,
    )

@dataclass
class StratuxConfig:
    enabled: bool = False
    host: str = "192.168.10.1"
    gdl90_port: int = 4000


@dataclass
class BlakePfdConfig:
    display: DisplayConfig
    sensors: SensorConfig
    features: FeatureConfig
    navigation: NavigationConfig
    airspeed: AirspeedConfig
    performance: AircraftPerformanceConfig
    altitude: AltitudeConfig
    synthetic_vision: SyntheticVisionConfig
    terrain: TerrainConfig
    stratux: StratuxConfig
    route: RouteConfig
    navigation_scaling: NavigationScalingConfig
    vnav: VnavConfig
    moving_map: MovingMapConfig
    obs: ObsConfig
    declutter: DeclutterConfig
    logging: LoggingConfig
    simulation: SimulationConfig
    fuel: FuelConfig
    audio_alerts: AudioAlertsConfig
    
@dataclass
class RouteConfig:
    auto_sequence: bool = True
    sequence_distance_nm: float = 1.0
@dataclass
class NavigationScalingConfig:
    mode: str = "enroute"
    enroute_full_scale_nm: float = 5.0
    terminal_full_scale_nm: float = 1.0
    approach_full_scale_nm: float = 0.3
@dataclass
class VnavConfig:
    enabled: bool = True
    glidepath_angle_deg: float = 3.0
@dataclass
class MovingMapConfig:
    range_nm: float = 25.0
@dataclass
class ObsConfig:
    enabled: bool = False
    selected_course_deg: float = 0.0
@dataclass
class DeclutterConfig:
    level: int = 0
@dataclass
class LoggingConfig:
    enabled: bool = True
    interval_s: float = 1.0
@dataclass
class SimulationConfig:
    profile: str = "straight"
    paused: bool = False
    reset_counter: int = 0
@dataclass
class FuelConfig:
    yellow_gal: float = 6.0
    red_gal: float = 3.0
    yellow_endurance_hr: float = 1.0
    red_endurance_hr: float = 0.5
    total_gal: float = 24.0
    remaining_gal: float = 24.0
@dataclass
class EmsTestConfig:
    mode: str = "normal"
@dataclass
class AudioAlertsConfig:
    enabled: bool = True
    buzzer_enabled: bool = True
    buzzer_pin: int = 18
    repeat_interval_s: float = 10.0


def load_config(path: Path = CONFIG_PATH) -> BlakePfdConfig:
    """
    Load Blake PFD YAML config.
    """
    
    if not path.exists():
        print(f"Config not found at {path}, using defaults.")
        raw: dict[str, Any] = {}
    else:
        raw = yaml.safe_load(path.read_text()) or {}
        
    return BlakePfdConfig(
        display=DisplayConfig(**raw.get("display", {})),
        sensors=SensorConfig(**raw.get("sensors", {})),
        features=FeatureConfig(**raw.get("features", {})),
        navigation=NavigationConfig(**raw.get("navigation", {})),
        airspeed=AirspeedConfig(**raw.get("airspeed", {})),
        performance=AircraftPerformanceConfig(
            **raw.get(
                "performance",
                {},
            )
        ),
        altitude=AltitudeConfig(
            **raw.get(
                "altitude",
                {},
            )
        ),
        synthetic_vision=SyntheticVisionConfig(
            **raw.get(
                "synthetic_vision",
                {},
            )
        ),
        terrain=TerrainConfig(
            **raw.get(
                "terrain",
                {},
            )
        ),
        stratux=StratuxConfig(
            **raw.get(
                "stratux",
                {},
            )
        ),
        route=RouteConfig(**raw.get("route", {})),
        navigation_scaling=NavigationScalingConfig(**raw.get("navigation_scaling", {})),
        vnav=VnavConfig(**raw.get("vnav", {})),
        moving_map=MovingMapConfig(**raw.get("moving_map", {})),
        obs=ObsConfig(**raw.get("obs", {})),
        declutter=DeclutterConfig(**raw.get("declutter", {})),
        simulation=SimulationConfig(**raw.get("simulation", {})),
        logging=LoggingConfig(**raw.get("logging", {})),
        fuel=FuelConfig(**raw.get("fuel", {})),
        audio_alerts=AudioAlertsConfig(**raw.get("audio_alerts", {})),
    )

def demo() -> None:
    config = load_config()

    print("===== Blake PFD Config Demo =====")
    print(config)
    
def get_cdi_full_scale_nm(config) -> float:
    mode = config.navigation_scaling.mode.lower()

    if mode == "approach":
        return config.navigation_scaling.approach_full_scale_nm

    if mode == "terminal":
        return config.navigation_scaling.terminal_full_scale_nm

    return config.navigation_scaling.enroute_full_scale_nm


if __name__ == "__main__":
    demo()