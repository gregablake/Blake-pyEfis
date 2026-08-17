from __future__ import annotations
from dataclasses import replace
import argparse
import sys
from time import monotonic
from math import cos, radians, sin
from pathlib import Path

import yaml
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF
from PyQt6.QtWidgets import QApplication, QWidget

from pyefis.user.blake_pfd.airport_info_page import AirportInfoPage
from pyefis.user.blake_pfd.audio_alerts import AudioAlertManager
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.core.page_manager import PageManager
from pyefis.user.blake_pfd.core.page_renderer import PageRenderer
from pyefis.user.blake_pfd.core.warning_manager import WarningManager
from pyefis.user.blake_pfd.database_importer import AviationDatabase
from pyefis.user.blake_pfd.ems_alert_history import EmsAlertHistory
from pyefis.user.blake_pfd.ems_page import EmsPage
from pyefis.user.blake_pfd.ems_trend_page import EmsTrendPage
from pyefis.user.blake_pfd.engine_checklist_page import EngineChecklistPage
from pyefis.user.blake_pfd.engine_sim import SimulatedEngineSource
from pyefis.user.blake_pfd.flight_computer import FlightComputer, FlightData
from pyefis.user.blake_pfd.flight_logger import FlightLogger
from pyefis.user.blake_pfd.fms_page import FmsPage
from pyefis.user.blake_pfd.hardware_readers import BlakeHardwareSensorSource
from pyefis.user.blake_pfd.log_replay import LogReplaySource
from pyefis.user.blake_pfd.master_warning import draw_master_warning_strip
from pyefis.user.blake_pfd.moving_map import MovingMapComputer
from pyefis.user.blake_pfd.nearest_page import NearestPage
from pyefis.user.blake_pfd.pages.map_page import (
    MapPage,
)
from pyefis.user.blake_pfd.pages.settings_page import (
    SettingsPage,
)
from pyefis.user.blake_pfd.obstacles import ObstacleComputer
from pyefis.user.blake_pfd.route_manager import RouteManager
from pyefis.user.blake_pfd.safe_taxi import SafeTaxiComputer
from pyefis.user.blake_pfd.sensors_sim import SimulatedSensorSource
from pyefis.user.blake_pfd.startup_check import run_startup_check
from pyefis.user.blake_pfd.stratux_reader import StratuxReader
from pyefis.user.blake_pfd.synthetic_vision import (
    SyntheticVisionComputer,
    project_object_to_screen,
)
from pyefis.user.blake_pfd.terrain import TerrainComputer
from pyefis.user.blake_pfd.weather_reader import WeatherReader
from pyefis.user.blake_pfd.core.event_manager import EventManager
from pyefis.user.blake_pfd.core.flight_state_manager import FlightStateManager
from pyefis.user.blake_pfd.core.sensor_manager import SensorManager
from pyefis.user.blake_pfd.core.aircraft_state_manager import AircraftStateManager
from pyefis.user.blake_pfd.core.checklist_manager import ChecklistManager
from pyefis.user.blake_pfd.core.engine_manager import EngineManager
from pyefis.user.blake_pfd.core.engine_analyzer import EngineAnalyzer
from pyefis.user.blake_pfd.core.engine_trend_manager import EngineTrendManager
from pyefis.user.blake_pfd.core.engine_state import EngineState
from pyefis.user.blake_pfd.core.cylinder_analyzer import CylinderAnalyzer
from pyefis.user.blake_pfd.core.engine_prediction import EnginePredictor
from pyefis.user.blake_pfd.core.engine_advisor import EngineAdvisor
from types import SimpleNamespace
from pyefis.user.blake_pfd.core.aircraft_systems_factory import (
    build_aircraft_systems,
)
from pyefis.user.blake_pfd.core.nearby_airport_provider import (
    NearbyAirportProvider,
)

from pyefis.user.blake_pfd.core.emergency_detection import (
    EmergencyDetection,
)

from pyefis.user.blake_pfd.core.landing_site_monitor import (
    LandingSiteMonitor,
)

from pyefis.user.blake_pfd.core.emergency_landing_planner import (
    EmergencyLandingPlanner,
)

from pyefis.user.blake_pfd.core.energy_state_calculator import (
    EnergyStateCalculator,
)

from pyefis.user.blake_pfd.core.terrain_source_factory import (
    build_terrain_source,
)
from pyefis.user.blake_pfd.core.terrain_profile_provider import (
    TerrainProfileProvider,
)
from pyefis.user.blake_pfd.core.terrain_awareness_manager import (
    TerrainAwarenessManager,
)

from pyefis.user.blake_pfd.core.terrain_startup_validator import (
    TerrainStartupValidator,
)
from pyefis.user.blake_pfd.core.terrain_alert_gate import (
    TerrainAlertGate,
)

from pyefis.user.blake_pfd.core.cfit_manager import (
    CfitManager,
)

from pyefis.user.blake_pfd.core.terrain_warning_presenter import (
    TerrainWarningPresenter,
)

from pyefis.user.blake_pfd.core.flight_path_marker import (
    FlightPathMarker,
)

from pyefis.user.blake_pfd.core.hits_guidance import (
    HitsGuidance,
)

from pyefis.user.blake_pfd.core.flight_director import (
    FlightDirector,
)

from pyefis.user.blake_pfd.core.touch_guidance_menu import (
    GuidanceTouchSettings,
    TouchGuidanceMenu,
)

from pyefis.user.blake_pfd.core.touch_navigation import (
    TouchNavigation,
)

from pyefis.user.blake_pfd.core.touch_settings import (
    TouchSettings,
)

from pyefis.user.blake_pfd.core.touch_map_controls import (
    TouchMapControls,
)

from pyefis.user.blake_pfd.core.map_viewport import (
    MapViewport,
)

from pyefis.user.blake_pfd.core.map_orientation import (
    MapOrientation,
)

from pyefis.user.blake_pfd.core.map_airport_selector import (
    MapAirportMarker,
    MapAirportSelector,
)

from pyefis.user.blake_pfd.core.direct_to import (
    DirectToManager,
)

from pyefis.user.blake_pfd.core.direct_to_guidance import (
    DirectToGuidance,
)

from pyefis.user.blake_pfd.core.direct_to_lateral_guidance import (
    DirectToLateralGuidance,
)

from pyefis.user.blake_pfd.core.guidance_settings_store import (
    save_guidance_touch_settings,
)

from pyefis.user.blake_pfd.core.sensor_watchdog import (
    SensorWatchdog,
)

class BlakePfdDemo(QWidget):
    def __init__(self, use_hardware: bool = False, replay_log: str | None = None) -> None:
        super().__init__()

        self.config = load_config()
        self.aircraft_systems = build_aircraft_systems(
            self.config
        )

        self.aircraft_intelligence = (
            self.aircraft_systems.aircraft_intelligence
        )

        self.emergency_airport_manager = (
            self.aircraft_systems.emergency_airport_manager
        )
        
        self.landing_site_monitor = LandingSiteMonitor()
        self.emergency_landing_planner = (
            EmergencyLandingPlanner(
                best_glide_speed_kt=80.0,
            )
        )
        
        self.energy_state_calculator = (
            EnergyStateCalculator(
                stable_trend_threshold_fpm=50.0,
            )
        )

        self.energy_state = (
            self.energy_state_calculator.calculate(
                altitude_ft=None,
                terrain_elevation_ft=0.0,
                airspeed_kt=0.0,
            )
        )
        
        self.landing_site_status = (
            self.landing_site_monitor.evaluate(
                selected_airport_distance_nm=None,
                max_glide_distance_nm=0.0,
            )
        )
        self.emergency_landing_plan = (
            self.emergency_landing_planner.create_plan(
                advice=None,
                emergency_active=False,
            )
        )
        
        self.direct_to_button_rect = QRectF()
        
        self.cancel_direct_to_button_rect = QRectF()

        self.reachable_airport_pipeline = (
            self.aircraft_systems.reachable_airport_pipeline
        )
        self.startup_status = run_startup_check()
        
        self.sensor_watchdog = SensorWatchdog()

        self.sensor_watchdog_state = (
            self.sensor_watchdog.evaluate(
                flight_data_available=False,
                position_valid=False,
            )
        )

        self.database = AviationDatabase()
        self.database.load_all()
        
        self.nearby_airport_provider = (
            NearbyAirportProvider(
                database=self.database,
                maximum_results=25,
            )
        )

        self.route_manager = RouteManager()
        self.flight_computer = FlightComputer()
        self.synthetic_vision = SyntheticVisionComputer()
        self.flight_path_marker = FlightPathMarker()

        self.flight_path_marker_state = (
            self.flight_path_marker.calculate(
                track_deg=0.0,
                heading_deg=0.0,
                ground_speed_kt=0.0,
                vertical_speed_fpm=0.0,
            )
        )
        
        self.hits_guidance = HitsGuidance(
            box_count=6,
        )

        self.hits_guidance_state = (
            self.hits_guidance.calculate(
                cdi=0.0,
                vdi=0.0,
                navigation_valid=False,
            )
        )
        
        self.flight_director = FlightDirector()

        self.flight_director_state = (
            self.flight_director.calculate(
                cdi=0.0,
                vdi=0.0,
                navigation_valid=False,
                enabled=False,
            )
        )
        
        self.touch_guidance_menu = (
            TouchGuidanceMenu()
        )

        self.guidance_touch_settings = (
            GuidanceTouchSettings(
                hits_enabled=(
                    self.config.guidance
                    .hits_enabled
                ),
                flight_director_enabled=(
                    self.config.guidance
                    .flight_director_enabled
                ),
                flight_path_marker_enabled=(
                    self.config.features
                    .show_flight_path_marker
                ),
                synthetic_vision_enabled=(
                    self.config.features
                    .show_synthetic_vision
                ),
            )
        )

        self.touch_guidance_menu_state = (
            self.touch_guidance_menu.state
        )
        
        self.touch_navigation = TouchNavigation()

        self.touch_navigation_state = (
            self.touch_navigation.layout(
                screen_width=(
                    self.config.display.width
                ),
                screen_height=(
                    self.config.display.height
                ),
                current_page="PFD",
            )
        )
        
        self.touch_settings = TouchSettings()

        self.touch_settings_state = (
            self.touch_settings.layout(
                screen_width=(
                    self.config.display.width
                ),
                screen_height=(
                    self.config.display.height
                ),
                values=(
                    self.guidance_touch_settings
                ),
            )
        )
        
        self.touch_map_controls = (
            TouchMapControls()
        )

        self.touch_map_state = (
            self.touch_map_controls.layout(
                screen_width=(
                    self.config.display.width
                ),
                screen_height=(
                    self.config.display.height
                ),
            )
        )
        
        self.touch_guidance_menu = (
            TouchGuidanceMenu()
        )
        
        self.guidance_touch_settings = (
            GuidanceTouchSettings(
                hits_enabled=(
                    self.config.guidance
                    .hits_enabled
                ),
                flight_director_enabled=(
                    self.config.guidance
                    .flight_director_enabled
                ),
                flight_path_marker_enabled=True,
                synthetic_vision_enabled=(
                    self.config.features
                    .show_synthetic_vision
                ),
            )
        )

        self.touch_guidance_menu_state = (
            self.touch_guidance_menu.state
        )

        self.safe_taxi = SafeTaxiComputer()
        self.moving_map = MovingMapComputer()

        self.map_range_nm = float(
            self.config.moving_map.range_nm
        )
        
        self.map_airport_selector = (
            MapAirportSelector(
                touch_radius_px=35.0,
            )
        )

        self.map_airport_selection = (
            self.map_airport_selector.selection
        )

        self.map_airport_markers = []
        
        self.map_viewport = MapViewport()
        
        self.map_orientation = (
            MapOrientation(
                mode="NORTH_UP",
            )
        )

        self.map_orientation_state = (
            self.map_orientation.state
        )

        self.map_viewport_state = (
            self.map_viewport.state
        )

        self.map_drag_active = False
        self.map_drag_last_x = 0.0
        self.map_drag_last_y = 0.0

        self.terrain = TerrainComputer()
        
        self.direct_to_manager = (
            DirectToManager()
        )

        self.direct_to_state = (
            self.direct_to_manager.state
        )
        
        self.direct_to_guidance = (
            DirectToGuidance()
        )

        self.direct_to_guidance_state = (
            self.direct_to_guidance.state
        )
        
        self.direct_to_lateral_guidance = (
            DirectToLateralGuidance(
                full_scale_error_deg=20.0,
            )
        )

        self.direct_to_lateral_guidance_state = (
            self.direct_to_lateral_guidance.state
        )

        self.terrain_source_bundle = (
            build_terrain_source(
                terrain_config=self.config.terrain,
                fallback_terrain=self.terrain,
            )
        )

        self.terrain_sampler = (
            self.terrain_source_bundle.sampler
        )

        self.terrain_source_name = (
            self.terrain_source_bundle.source_name
        )

        self.real_terrain_enabled = (
            self.terrain_source_bundle
            .real_terrain_enabled
        )

        self.terrain_source_message = (
            self.terrain_source_bundle.message
        )

        self.terrain_profile_provider = (
            TerrainProfileProvider(
                elevation_sampler=self.terrain_sampler,
                sample_distances_nm=tuple(
                    self.config.terrain
                    .sample_distances_nm
                ),
            )
        )

        self.terrain_awareness_manager = (
            TerrainAwarenessManager(
                profile_provider=(
                    self.terrain_profile_provider
                ),
            )
        )

        self.terrain_awareness_state = (
            self.terrain_awareness_manager.state
        )
        
        self.terrain_startup_validator = (
            TerrainStartupValidator()
        )

        self.terrain_startup_status = (
            self.terrain_startup_validator.validate(
                terrain_config=self.config.terrain,
            )
        )

        self.terrain_alert_gate = (
            TerrainAlertGate()
        )

        self.terrain_alert_state = (
            self.terrain_alert_gate.evaluate(
                startup_status=(
                    self.terrain_startup_status
                ),
                terrain_awareness_state=(
                    self.terrain_awareness_state
                ),
                real_terrain_enabled=(
                    self.real_terrain_enabled
                ),
            )
        )
        
        self.cfit_manager = CfitManager()
        self.cfit_state = self.cfit_manager.state
        
        self.terrain_warning_presenter = (
            TerrainWarningPresenter()
        )

        self.terrain_warning_presentation = (
            self.terrain_warning_presenter.build(
                terrain_alert_state=(
                    self.terrain_alert_state
                ),
                cfit_state=self.cfit_state,
            )
        )

        self.obstacles = ObstacleComputer()
        self.weather = WeatherReader()
        self.event_manager = EventManager(self)
        self.flight_state_manager = FlightStateManager()
        self.flight_state = self.flight_state_manager.state
        self.page_manager = PageManager()
        self.page_renderer = PageRenderer(self)
        self.warning_manager = WarningManager(self)

        self.fms_page = FmsPage()
        self.airport_info_page = AirportInfoPage()
        self.nearest_page = NearestPage()
        self.map_page = MapPage()
        self.settings_page = SettingsPage()
        self.ems_page = EmsPage()
        self.ems_trend_page = EmsTrendPage()
        self.ems_alert_history = EmsAlertHistory()
        self.engine_checklist_page = EngineChecklistPage()
        self.aircraft_state_manager = AircraftStateManager()
        self.emergency_airport_state = (
            self.emergency_airport_manager.state
        )
        self.aircraft = self.aircraft_state_manager.state
        self.pilot_emergency_selected = False

        # Initialize the emergency detection system
        self.emergency_detection = EmergencyDetection()

        self.emergency_status = (
            self.emergency_detection.evaluate(
                engine_state=None,
                flight_state=None,
                pilot_selected=(
                    self.pilot_emergency_selected
                ),
            )
        )
        self.checklist_manager = ChecklistManager()
        self.checklist_state = self.checklist_manager.state
        self.sensor_manager = SensorManager(
            flight_computer=self.flight_computer,
            use_hardware=use_hardware,
            replay_log=replay_log,
        )
        self.engine_manager = EngineManager()
        self.engine_trend_manager = EngineTrendManager()
        self.engine_analyzer = EngineAnalyzer()
        self.cylinder_analyzer = CylinderAnalyzer()
        self.engine_predictor = EnginePredictor()
        self.engine_advisor = EngineAdvisor()
        self.aircraft_recommendation = self.aircraft_intelligence.analyze(self.aircraft)
        self.last_aircraft_recommendation_key = (
            self.aircraft_recommendation.severity,
            self.aircraft_recommendation.title,
        )
        self.update_engine_state()
        self.use_hardware = use_hardware
        self.engine_manager = EngineManager()
        self.flight_logger = FlightLogger(
            log_interval_s=self.config.logging.interval_s,
        )
        self.engine_analyzer = EngineAnalyzer()
        
        self.audio_alerts = AudioAlertManager(
            enabled=self.config.audio_alerts.enabled,
            buzzer_enabled=self.config.audio_alerts.buzzer_enabled,
            buzzer_pin=self.config.audio_alerts.buzzer_pin,
            repeat_interval_s=self.config.audio_alerts.repeat_interval_s,
        )
        self.stratux = StratuxReader(
            host=self.config.stratux.host,
            port=self.config.stratux.gdl90_port,
        )
        self.pfd: FlightData | None = None

        self.register_pages()

        mode_name = "Replay" if replay_log else ("Hardware" if use_hardware else "Simulator")
        self.setWindowTitle(f"Blake PFD Demo - {mode_name}")
        self.resize(self.config.display.width, self.config.display.height)

        if self.config.display.fullscreen:
            self.showFullScreen()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)

    def register_pages(self) -> None:
        self.page_manager.register("PFD", "P")
        self.page_manager.register(
            "MAP",
            "M",
        )
        self.page_manager.register("FMS", "F")
        self.page_manager.register("AIRPORT", "A")
        self.page_manager.register("NEAREST", "N")
        self.page_manager.register("EMS", "E")
        self.page_manager.register("EMS_TREND", "T")
        self.page_manager.register("EMS_ALERTS", "H")
        self.page_manager.register("ENGINE_CHECKLIST", "C")
        self.page_manager.register(
            "SETTINGS",
            "S",
        )
        
    def update_engine_state(self) -> None:
        self.engine_data = self.sensor_manager.read_engine()

        self.engine_health = self.engine_manager.update(
            self.engine_data
        )

        self.engine_trend = self.engine_trend_manager.update(
            self.engine_data
        )

        self.engine_analysis = self.engine_analyzer.analyze(
            self.engine_data,
            self.engine_health,
            self.engine_trend,
        )
        self.cylinder_analysis = self.cylinder_analyzer.analyze(
            self.engine_data
        )
        
        self.engine_prediction = self.engine_predictor.predict(
            self.engine_trend
        )
        
        self.engine_advice = self.engine_advisor.advise(
            engine_state=SimpleNamespace(
                data=self.engine_data,
                health=self.engine_health,
                trend=self.engine_trend,
                analysis=self.engine_analysis,
                cylinders=self.cylinder_analysis,
                prediction=self.engine_prediction,
            ),
            flight_state=getattr(self, "flight_state", None),
        )

        self.engine_state = EngineState(
            data=self.engine_data,
            health=self.engine_health,
            trend=self.engine_trend,
            analysis=self.engine_analysis,
            cylinders=self.cylinder_analysis,
            prediction=self.engine_prediction,
            advice=self.engine_advice,
        )
        
    def activate_pilot_emergency(self) -> None:
        self.pilot_emergency_selected = True

        self.flight_state_manager.event_log.write(
            "EMERGENCY_MODE",
            "Pilot manually activated emergency mode.",
        )


    def cancel_pilot_emergency(self) -> None:
        self.pilot_emergency_selected = False

        self.flight_state_manager.event_log.write(
            "EMERGENCY_MODE",
            "Pilot manually cancelled emergency mode.",
        )

    def update_data(self) -> None:
        self.pfd = self.sensor_manager.read_flight()
        self.update_engine_state()

        if self.use_hardware:
            hardware_status = getattr(
                self.sensor_manager.flight_sensor_source,
                "status",
                None,
            )

            if hardware_status is not None:
                attitude_valid = (
                    hardware_status.bno085_ok
                )

                air_data_valid = (
                    hardware_status.baro_ok
                    and hardware_status.airspeed_ok
                )

                position_valid = (
                    hardware_status.gps_ok
                    and self.pfd is not None
                    and self.pfd.position_valid
                )
            else:
                attitude_valid = False
                air_data_valid = False
                position_valid = False

        else:
            attitude_valid = True
            air_data_valid = True

            position_valid = (
                self.pfd.position_valid
                if self.pfd is not None
                else False
            )

        self.sensor_watchdog_state = (
            self.sensor_watchdog.evaluate(
                flight_data_available=(
                    self.pfd is not None
                ),
                position_valid=position_valid,
                attitude_valid=attitude_valid,
                air_data_valid=air_data_valid,
            )
        )

        engine = self.engine_state.data

        if self.pfd is not None:
            engine.fuel_range_nm = (
                engine.endurance_hr * self.pfd.ground_speed_kt
            )

            self.flight_state = self.flight_state_manager.update(
                self.pfd,
                engine=engine,
            )
            
            self.flight_path_marker_state = (
                self.flight_path_marker.calculate(
                    track_deg=self.pfd.track_deg,
                    heading_deg=self.pfd.heading_deg,
                    ground_speed_kt=(
                        self.pfd.ground_speed_kt
                    ),
                    vertical_speed_fpm=(
                        self.pfd.vsi_fpm
                    ),
                )
            )
            
            self.hits_guidance_state = (
                self.hits_guidance.calculate(
                    cdi=self.pfd.cdi,
                    vdi=self.pfd.vdi,
                    navigation_valid=(
                        self.pfd.position_valid
                        and (
                            self.guidance_touch_settings
                            .hits_enabled
                        )
                    ),
                )
            )
            
            self.emergency_status = (
                self.emergency_detection.evaluate(
                    engine_state=self.engine_state,
                    flight_state=self.flight_state,
                    pilot_selected=(
                        self.pilot_emergency_selected
                    ),
                )
            )
            
        if (
            self.direct_to_state.active
            and self.pfd is not None
            and self.pfd.position_valid
        ):
            self.direct_to_state = (
                self.direct_to_manager.update(
                    aircraft_lat_deg=(
                        self.pfd.latitude_deg
                    ),
                    aircraft_lon_deg=(
                        self.pfd.longitude_deg
                    ),
                )
            )
            
        if (
            self.pfd is not None
            and self.pfd.position_valid
        ):
            self.direct_to_guidance_state = (
                self.direct_to_guidance.update(
                    direct_to_state=(
                        self.direct_to_state
                    ),
                    aircraft_track_deg=(
                        self.pfd.track_deg
                    ),
                )
            )
        else:
            self.direct_to_guidance_state = (
                self.direct_to_guidance.clear()
            )

        self.direct_to_lateral_guidance_state = (
            self.direct_to_lateral_guidance.update(
                guidance_state=(
                    self.direct_to_guidance_state
                ),
            )
        )
        
        if self.pfd is not None:
            if (
                self.direct_to_lateral_guidance_state.active
            ):
                flight_director_cdi = (
                    self.direct_to_lateral_guidance_state
                    .lateral_error
                )
            else:
                flight_director_cdi = (
                    self.pfd.cdi
                )

            self.flight_director_state = (
                self.flight_director.calculate(
                    cdi=flight_director_cdi,
                    vdi=self.pfd.vdi,
                    navigation_valid=(
                        self.pfd.position_valid
                    ),
                    enabled=(
                        self.guidance_touch_settings
                        .flight_director_enabled
                    ),
                )
            )

        if self.pfd is not None:
            # ---------------------------------------------------------
            # Emergency airport analysis
            # ---------------------------------------------------------
            if self.pfd.position_valid:
                nearby_airports = (
                    self.nearby_airport_provider.get_nearby_airports(
                        aircraft_lat_deg=(
                            self.pfd.latitude_deg
                        ),
                        aircraft_lon_deg=(
                            self.pfd.longitude_deg
                        ),
                    )
                )

                self.emergency_airport_state = (
                    self.emergency_airport_manager.update(
                        airports=nearby_airports,
                        aircraft_altitude_ft=(
                            self.pfd.pressure_alt_ft
                        ),
                        terrain_elevation_ft=0.0,
                        wind_speed_kt=(
                            self.pfd.wind_speed_kt
                        ),
                        wind_from_deg=(
                            self.pfd.wind_direction_deg
                        ),
                        emergency_active=(
                            self.emergency_status.active
                        ),
                    )
                )

                advice = (
                    self.emergency_airport_state.advice
                )

                self.landing_site_status = (
                    self.landing_site_monitor.evaluate(
                        selected_airport_distance_nm=(
                            advice.distance_nm
                        ),
                        max_glide_distance_nm=(
                            self.emergency_airport_state
                            .result
                            .glide_range_nm
                        ),
                    )
                )

                self.emergency_landing_plan = (
                    self.emergency_landing_planner.create_plan(
                        advice=advice,
                        emergency_active=(
                            self.emergency_status.active
                        ),
                        ground_speed_kt=(
                            self.pfd.ground_speed_kt
                        ),
                    )
                )

            else:
                self.emergency_airport_manager.clear()

                self.emergency_airport_state = (
                    self.emergency_airport_manager.state
                )

                self.landing_site_status = (
                    self.landing_site_monitor.evaluate(
                        selected_airport_distance_nm=None,
                        max_glide_distance_nm=0.0,
                    )
                )

                self.emergency_landing_plan = (
                    self.emergency_landing_planner.create_plan(
                        advice=None,
                        emergency_active=False,
                    )
                )

            if self.pfd.position_valid:
                self.terrain_startup_status = (
                    self.terrain_startup_validator.validate(
                        terrain_config=(
                            self.config.terrain
                        ),
                        aircraft_lat_deg=(
                            self.pfd.latitude_deg
                        ),
                        aircraft_lon_deg=(
                            self.pfd.longitude_deg
                        ),
                    )
                )

                self.terrain_awareness_state = (
                    self.terrain_awareness_manager.update(
                        aircraft_lat_deg=(
                            self.pfd.latitude_deg
                        ),
                        aircraft_lon_deg=(
                            self.pfd.longitude_deg
                        ),
                        course_deg=(
                            self.pfd.track_deg
                        ),
                        aircraft_altitude_ft=(
                            self.pfd.pressure_alt_ft
                        ),
                        vertical_speed_fpm=(
                            self.pfd.vsi_fpm
                        ),
                        ground_speed_kt=(
                            self.pfd.ground_speed_kt
                        ),
                        position_valid=True,
                    )
                )

            else:
                self.terrain_awareness_manager.clear()

                self.terrain_awareness_state = (
                    self.terrain_awareness_manager.state
                )

            self.terrain_alert_state = (
                self.terrain_alert_gate.evaluate(
                    startup_status=(
                        self.terrain_startup_status
                    ),
                    terrain_awareness_state=(
                        self.terrain_awareness_state
                    ),
                    real_terrain_enabled=(
                        self.real_terrain_enabled
                    ),
                )
            )
            
            terrain_profile = (
                self.terrain_awareness_state.profile
            )

            cfit_inputs_valid = (
                self.pfd.position_valid
                and self.real_terrain_enabled
                and (
                    self.terrain_startup_status
                    .predictive_alerts_enabled
                )
                and self.terrain_awareness_state.valid
                and bool(terrain_profile.points)
            )

            if cfit_inputs_valid:
                self.cfit_state = (
                    self.cfit_manager.update(
                        aircraft_altitude_ft=(
                            self.pfd.pressure_alt_ft
                        ),
                        vertical_speed_fpm=(
                            self.pfd.vsi_fpm
                        ),
                        ground_speed_kt=(
                            self.pfd.ground_speed_kt
                        ),
                        terrain_profile=(
                            terrain_profile
                        ),
                    )
                )
            else:
                self.cfit_manager.clear()
                self.cfit_state = (
                    self.cfit_manager.state
                )
                
            self.terrain_warning_presentation = (
                self.terrain_warning_presenter.build(
                    terrain_alert_state=(
                        self.terrain_alert_state
                    ),
                    cfit_state=self.cfit_state,
                )
            )

            selected_site_distance_nm = getattr(
                self.emergency_landing_plan,
                "distance_nm",
                None,
            )

            glide_range_nm = getattr(
                self.emergency_airport_state.result,
                "glide_range_nm",
                None,
            )

            terrain_elevation_ft = 0.0

            if self.terrain_awareness_state.valid:
                profile_points = (
                    self.terrain_awareness_state
                    .profile
                    .points
                )

                if profile_points:
                    terrain_elevation_ft = (
                        profile_points[0].elevation_ft
                    )

            self.energy_state = (
                self.energy_state_calculator.calculate(
                    altitude_ft=(
                        self.pfd.pressure_alt_ft
                    ),
                    terrain_elevation_ft=(
                        terrain_elevation_ft
                    ),
                    airspeed_kt=(
                        self.pfd.ias_kt
                    ),
                    timestamp_s=monotonic(),
                    selected_site_distance_nm=(
                        selected_site_distance_nm
                    ),
                    glide_range_nm=glide_range_nm,
                    target_altitude_ft=None,
                )
            )

            self.checklist_state = (
                self.checklist_manager.update(
                    self.flight_state.phase
                )
            )

            self.engine_checklist_page.set_phase_by_name(
                self.flight_state.phase
            )

            if self.checklist_state.should_popup:
                self.page_manager.set_page(
                    "ENGINE_CHECKLIST"
                )

            self.aircraft = (
                self.aircraft_state_manager.update(
                    pfd=self.pfd,
                    engine=engine,
                    flight_state=self.flight_state,
                    engine_state=self.engine_state,
                    selected_waypoint_id=(
                        self.config.navigation.selected_waypoint_id
                    ),
                    wind_speed_kt=(
                        self.pfd.wind_speed_kt
                    ),
                    wind_from_deg=(
                        self.pfd.wind_direction_deg
                    ),
                    emergency_airport_state=(
                        self.emergency_airport_state
                    ),
                )
            )

        self.aircraft_recommendation = (
            self.aircraft_intelligence.analyze(
                self.aircraft
            )
        )

        recommendation_key = (
            self.aircraft_recommendation.severity,
            self.aircraft_recommendation.title,
        )

        if (
            recommendation_key
            != self.last_aircraft_recommendation_key
        ):
            self.flight_state_manager.event_log.write(
                "AI_RECOMMENDATION",
                (
                    f"{self.aircraft_recommendation.severity}: "
                    f"{self.aircraft_recommendation.title} - "
                    f"{self.aircraft_recommendation.message}"
                ),
            )

            self.last_aircraft_recommendation_key = (
                recommendation_key
            )

        self.ems_alert_history.update(engine)
        self.ems_trend_page.add_sample(engine)

        self.audio_alerts.update(
            engine,
            silenced=self.ems_alert_history.silenced,
        )

        if (
            self.config.logging.enabled
            and self.pfd is not None
        ):
            self.flight_logger.maybe_log(
                self.pfd,
                waypoint_id=(
                    self.config.navigation.selected_waypoint_id
                ),
                engine=engine,
            )

        self.update()

    def mousePressEvent(
        self,
        event,
    ) -> None:  # noqa: N802
        position = event.position()

        touch_x = position.x()
        touch_y = position.y()

        self.touch_navigation_state = (
            self.touch_navigation.layout(
                screen_width=self.width(),
                screen_height=self.height(),
                current_page=(
                    self.page_manager.current()
                ),
            )
        )

        selected_page = (
            self.touch_navigation.page_for_touch(
                point_x=touch_x,
                point_y=touch_y,
            )
        )

        if selected_page is not None:
            self.page_manager.set_page(
                selected_page
            )

            self.touch_navigation_state = (
                self.touch_navigation.layout(
                    screen_width=self.width(),
                    screen_height=self.height(),
                    current_page=selected_page,
                )
            )

            self.update()
            event.accept()
            return
        
        if (
            self.page_manager.current()
            == "MAP"
        ):
            self.touch_map_state = (
                self.touch_map_controls.layout(
                    screen_width=self.width(),
                    screen_height=self.height(),
                )
            )

            map_action = (
                self.touch_map_controls
                .action_for_touch(
                    point_x=touch_x,
                    point_y=touch_y,
                )
            )

            if map_action == "zoom_in":
                self.map_range_nm = max(
                    2.0,
                    self.map_range_nm / 2.0,
                )

                self.update()
                event.accept()
                return

            if map_action == "zoom_out":
                self.map_range_nm = min(
                    200.0,
                    self.map_range_nm * 2.0,
                )

                self.update()
                event.accept()
                return

            if map_action == "center":
                self.map_viewport_state = (
                    self.map_viewport.center()
                )

                self.update()
                event.accept()
                return
            
            if map_action == "orientation":
                self.map_orientation_state = (
                    self.map_orientation.toggle()
                )

                if self.pfd is not None:
                    self.map_orientation_state = (
                        self.map_orientation
                        .update_reference(
                            track_deg=(
                                self.pfd.track_deg
                            ),
                        )
                    )

                self.update()
                event.accept()
                return
            
            if (
                self.direct_to_state.active
                and (
                    self.cancel_direct_to_button_rect
                    .contains(
                        QPointF(
                            touch_x,
                            touch_y,
                        )
                    )
                )
            ):
                self.direct_to_state = (
                    self.direct_to_manager.clear()
                )
                
                self.direct_to_guidance_state = (
                    self.direct_to_guidance.clear()
                )
                
                self.direct_to_lateral_guidance_state = (
                    self.direct_to_lateral_guidance.clear()
                )

                self.update()
                event.accept()
                return
            
            if (
                self.map_airport_selection.selected
                and self.direct_to_button_rect.contains(
                    QPointF(
                        touch_x,
                        touch_y,
                    )
                )
            ):
                identifier = (
                    self.map_airport_selection
                    .identifier
                )

                airport = (
                    self.database.get_airport(
                        identifier
                    )
                    if identifier
                    else None
                )

                if (
                    airport is not None
                    and self.pfd is not None
                ):
                    self.direct_to_state = (
                        self.direct_to_manager.activate(
                            aircraft_lat_deg=(
                                self.pfd.latitude_deg
                            ),
                            aircraft_lon_deg=(
                                self.pfd.longitude_deg
                            ),
                            target_identifier=(
                                airport.ident
                            ),
                            target_name=(
                                airport.name
                            ),
                            target_lat_deg=(
                                airport.lat_deg
                            ),
                            target_lon_deg=(
                                airport.lon_deg
                            ),
                        )
                    )

                    self.update()

                event.accept()
                return
            
            if map_action is None:
                selection = (
                    self.map_airport_selector
                    .select_at(
                        point_x=touch_x,
                        point_y=touch_y,
                        markers=(
                            self.map_airport_markers
                        ),
                    )
                )

                self.map_airport_selection = (
                    selection
                )

                if selection.selected:
                    self.update()
                    event.accept()
                    return

                self.map_drag_active = True
                self.map_drag_last_x = touch_x
                self.map_drag_last_y = touch_y

                event.accept()
                return
        
        if (
            self.page_manager.current()
            == "SETTINGS"
        ):
            self.touch_settings_state = (
                self.touch_settings.layout(
                    screen_width=self.width(),
                    screen_height=self.height(),
                    values=(
                        self.guidance_touch_settings
                    ),
                )
            )

            settings_key = (
                self.touch_settings.key_for_touch(
                    point_x=touch_x,
                    point_y=touch_y,
                )
            )

            if settings_key is not None:
                current_value = bool(
                    getattr(
                        self.guidance_touch_settings,
                        settings_key,
                    )
                )


                self.guidance_touch_settings = replace(
                    self.guidance_touch_settings,
                    **{
                        settings_key: (
                            not current_value
                        ),
                    },
                )

                save_guidance_touch_settings(
                    self.guidance_touch_settings
                )

                self.touch_settings_state = (
                    self.touch_settings.layout(
                        screen_width=self.width(),
                        screen_height=self.height(),
                        values=(
                            self.guidance_touch_settings
                        ),
                    )
                )

                self.update()
                event.accept()
                return

        button_width = 150.0
        button_height = 52.0
        margin = 16.0

        guidance_button_x = (
            self.width()
            - button_width
            - margin
        )

        guidance_button_y = (
            self.height()
            - button_height
            - margin
        )

        guidance_button = QRectF(
            guidance_button_x,
            guidance_button_y,
            button_width,
            button_height,
        )

        if guidance_button.contains(
            QPointF(
                touch_x,
                touch_y,
            )
        ):
            self.touch_guidance_menu_state = (
                self.touch_guidance_menu
                .toggle_visibility(
                    screen_width=self.width(),
                    screen_height=self.height(),
                    settings=(
                        self.guidance_touch_settings
                    ),
                )
            )

            self.update()
            event.accept()
            return

        if self.touch_guidance_menu_state.visible:
            previous_settings = (
                self.guidance_touch_settings
            )

            self.touch_guidance_menu_state = (
                self.touch_guidance_menu
                .handle_touch(
                    point_x=touch_x,
                    point_y=touch_y,
                )
            )

            self.guidance_touch_settings = (
                self.touch_guidance_menu_state
                .settings
            )

            if (
                self.guidance_touch_settings
                != previous_settings
            ):
                save_guidance_touch_settings(
                    self.guidance_touch_settings
                )

                self.update()

            event.accept()
            return

        super().mousePressEvent(
            event
        )
        
    def mouseMoveEvent(
        self,
        event,
    ) -> None:  # noqa: N802
        if (
            not self.map_drag_active
            or self.page_manager.current()
            != "MAP"
        ):
            super().mouseMoveEvent(
                event
            )
            return

        position = event.position()

        touch_x = position.x()
        touch_y = position.y()

        delta_x = (
            touch_x
            - self.map_drag_last_x
        )

        delta_y = (
            touch_y
            - self.map_drag_last_y
        )

        self.map_drag_last_x = touch_x
        self.map_drag_last_y = touch_y

        self.map_viewport_state = (
            self.map_viewport.pan_by(
                delta_x_px=delta_x,
                delta_y_px=delta_y,
            )
        )

        self.update()
        event.accept()
        
    def mouseReleaseEvent(
        self,
        event,
    ) -> None:  # noqa: N802
        if self.map_drag_active:
            self.map_drag_active = False

            event.accept()
            return

        super().mouseReleaseEvent(
            event
        )
        
    def mouseReleaseEvent(
        self,
        event,
    ) -> None:  # noqa: N802
        if self.map_drag_active:
            self.map_drag_active = False

            event.accept()
            return

        super().mouseReleaseEvent(
            event
        )
        
    def keyPressEvent(
        self,
        event,
    ) -> None:  # noqa: N802
        self.event_manager.handle_key(
            event
        )
        self.update()

    def page_name_from_key(self, key: Qt.Key) -> str | None:
        key_map = {
            Qt.Key.Key_P: "PFD",
            Qt.Key.Key_F: "FMS",
            Qt.Key.Key_A: "AIRPORT",
            Qt.Key.Key_N: "NEAREST",
            Qt.Key.Key_E: "EMS",
            Qt.Key.Key_T: "EMS_TREND",
            Qt.Key.Key_H: "EMS_ALERTS",
            Qt.Key.Key_C: "ENGINE_CHECKLIST",
        }
        return key_map.get(key)

    def activate_direct_to(self, waypoint_id: str) -> None:
        waypoint_id = waypoint_id.upper()
        print(f"Activating Direct-To {waypoint_id}")

        self.config.navigation.selected_waypoint_id = waypoint_id
        self.flight_computer.config.navigation.selected_waypoint_id = waypoint_id

    def cycle_ems_test_mode(self) -> None:
        modes = [
            "normal",
            "high_cht",
            "high_egt",
            "low_oil",
            "alt_fail",
            "ign_fail",
            "low_fuel",
        ]

        current = getattr(self.config.ems_test, "mode", "normal")

        try:
            index = modes.index(current)
        except ValueError:
            index = 0

        next_mode = modes[(index + 1) % len(modes)]

        config_path = Path(__file__).with_name("pfd_config.yaml")
        raw = yaml.safe_load(config_path.read_text()) or {}
        raw.setdefault("ems_test", {})
        raw["ems_test"]["mode"] = next_mode
        config_path.write_text(yaml.safe_dump(raw, sort_keys=False))

        self.config = load_config()
        self.flight_computer.config = self.config

        print(f"EMS test mode: {next_mode}")
        
    def draw_terrain_warning_banner(
        self,
        painter,
        width: int,
        height: int,
    ) -> None:

        presentation = (
            self.terrain_warning_presentation
        )

        if not presentation.visible:
            return

        if presentation.priority == "CRITICAL":
            color = QColor(220, 0, 0)

        elif presentation.priority == "WARNING":
            color = QColor(190, 30, 30)

        else:
            color = QColor(255, 180, 0)

        box_height = 72

        painter.fillRect(
            0,
            0,
            width,
            box_height,
            color,
        )

        painter.setPen(Qt.GlobalColor.white)

        font = painter.font()

        font.setBold(True)
        font.setPointSize(22)

        painter.setFont(font)

        painter.drawText(
            20,
            28,
            presentation.title,
        )

        font.setPointSize(18)

        painter.setFont(font)

        painter.drawText(
            20,
            55,
            presentation.message,
        )

        if presentation.detail:

            font.setBold(False)
            font.setPointSize(11)

            painter.setFont(font)

            painter.drawText(
                width - 250,
                55,
                presentation.detail,
            )
            
    def draw_hits_guidance(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        state = self.hits_guidance_state

        if not state.valid:
            return

        if not state.boxes:
            return

        painter.save()

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        for box in reversed(
            state.boxes
        ):
            center_x = (
                box.center_x_fraction
                * width
            )

            center_y = (
                box.center_y_fraction
                * height
            )

            box_width = (
                box.width_fraction
                * width
            )

            box_height = (
                box.height_fraction
                * height
            )

            left = (
                center_x
                - box_width / 2.0
            )

            top = (
                center_y
                - box_height / 2.0
            )

            line_width = (
                3.0
                - box.depth_fraction
                * 1.5
            )

            opacity = int(
                255
                - box.depth_fraction
                * 100
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        0,
                        255,
                        opacity,
                    ),
                    max(
                        1.0,
                        line_width,
                    ),
                )
            )

            painter.drawRect(
                QRectF(
                    left,
                    top,
                    box_width,
                    box_height,
                )
            )

        painter.restore()
         
    def draw_flight_director(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        state = self.flight_director_state

        if not state.valid or not state.active:
            return

        pixels_per_degree = 6.0

        center_x = width / 2.0
        center_y = height / 2.0

        roll_offset_px = (
            state.roll_command_deg
            * pixels_per_degree
        )

        pitch_offset_px = (
            state.pitch_command_deg
            * pixels_per_degree
        )

        command_x = (
            center_x
            + roll_offset_px
        )

        command_y = (
            center_y
            - pitch_offset_px
        )

        command_x = max(
            80.0,
            min(
                width - 80.0,
                command_x,
            ),
        )

        command_y = max(
            100.0,
            min(
                height - 100.0,
                command_y,
            ),
        )

        horizontal_bar_half_width = 55.0
        vertical_bar_half_height = 42.0
        center_gap = 12.0

        painter.save()

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    0,
                    255,
                ),
                6,
            )
        )

        painter.drawLine(
            QPointF(
                command_x
                - horizontal_bar_half_width,
                command_y,
            ),
            QPointF(
                command_x
                - center_gap,
                command_y,
            ),
        )

        painter.drawLine(
            QPointF(
                command_x
                + center_gap,
                command_y,
            ),
            QPointF(
                command_x
                + horizontal_bar_half_width,
                command_y,
            ),
        )

        painter.drawLine(
            QPointF(
                command_x,
                command_y
                - vertical_bar_half_height,
            ),
            QPointF(
                command_x,
                command_y
                - center_gap,
            ),
        )

        painter.drawLine(
            QPointF(
                command_x,
                command_y
                + center_gap,
            ),
            QPointF(
                command_x,
                command_y
                + vertical_bar_half_height,
            ),
        )

        painter.restore()   
    
    def draw_flight_path_marker(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        marker = self.flight_path_marker_state

        if not marker.valid:
            return

        pixels_per_degree = 8.0

        center_x = width / 2.0
        center_y = height / 2.0

        marker_x = (
            center_x
            + marker.x_offset_deg
            * pixels_per_degree
        )

        marker_y = (
            center_y
            + marker.y_offset_deg
            * pixels_per_degree
        )

        marker_x = max(
            35.0,
            min(
                width - 35.0,
                marker_x,
            ),
        )

        marker_y = max(
            85.0,
            min(
                height - 85.0,
                marker_y,
            ),
        )

        radius = 10.0
        wing_length = 14.0
        tail_length = 10.0

        painter.save()

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    0,
                    255,
                    120,
                ),
                3,
            )
        )

        painter.drawEllipse(
            QPointF(
                marker_x,
                marker_y,
            ),
            radius,
            radius,
        )

        painter.drawLine(
            QPointF(
                marker_x - radius - wing_length,
                marker_y,
            ),
            QPointF(
                marker_x - radius,
                marker_y,
            ),
        )

        painter.drawLine(
            QPointF(
                marker_x + radius,
                marker_y,
            ),
            QPointF(
                marker_x + radius + wing_length,
                marker_y,
            ),
        )

        painter.drawLine(
            QPointF(
                marker_x,
                marker_y + radius,
            ),
            QPointF(
                marker_x,
                marker_y + radius + tail_length,
            ),
        )

        painter.restore()
        
    def draw_map_airport_selection(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        selection = (
            self.map_airport_selection
        )

        if not selection.selected:
            self.direct_to_button_rect = QRectF()
            self.cancel_direct_to_button_rect = QRectF()
            return

        card_x = 350.0
        card_y = 95.0
        card_width = 360.0
        card_height = 255.0

        painter.save()

        painter.setBrush(
            QBrush(
                QColor(
                    15,
                    20,
                    28,
                    240,
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    0,
                    220,
                    255,
                ),
                2,
            )
        )

        painter.drawRoundedRect(
            QRectF(
                card_x,
                card_y,
                card_width,
                card_height,
            ),
            10.0,
            10.0,
        )

        font = painter.font()
        font.setBold(True)
        font.setPointSize(17)
        painter.setFont(font)

        painter.setPen(
            QColor(
                0,
                220,
                255,
            )
        )

        painter.drawText(
            QRectF(
                card_x + 15.0,
                card_y + 10.0,
                card_width - 30.0,
                32.0,
            ),
            Qt.AlignmentFlag.AlignLeft,
            selection.identifier or "",
        )

        font.setPointSize(11)
        painter.setFont(font)

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        painter.drawText(
            QRectF(
                card_x + 15.0,
                card_y + 45.0,
                card_width - 30.0,
                26.0,
            ),
            Qt.AlignmentFlag.AlignLeft,
            selection.name,
        )

        distance_nm = (
            selection.distance_nm
            if selection.distance_nm is not None
            else 0.0
        )

        bearing_deg = (
            selection.bearing_deg
            if selection.bearing_deg is not None
            else 0.0
        )

        painter.drawText(
            QRectF(
                card_x + 15.0,
                card_y + 78.0,
                card_width - 30.0,
                26.0,
            ),
            Qt.AlignmentFlag.AlignLeft,
            (
                f"DIST {distance_nm:.1f} NM    "
                f"BRG {bearing_deg:.0f}°"
            ),
        )

        painter.setPen(
            QColor(
                180,
                180,
                180,
            )
        )

        painter.drawText(
            QRectF(
                card_x + 15.0,
                card_y + 108.0,
                card_width - 30.0,
                24.0,
            ),
            Qt.AlignmentFlag.AlignLeft,
            "AIRPORT SELECTED",
        )

        if self.direct_to_state.active:
            dto_ident = (
                self.direct_to_state.identifier
                or ""
            )

            painter.setPen(
                QColor(
                    0,
                    255,
                    120,
                )
            )

            painter.drawText(
                QRectF(
                    card_x + 15.0,
                    card_y + 130.0,
                    card_width - 30.0,
                    22.0,
                ),
                Qt.AlignmentFlag.AlignLeft,
                f"DTO ACTIVE → {dto_ident}",
            )

        direct_button_x = (
            card_x + 15.0
        )
        direct_button_y = (
            card_y + 155.0
        )
        direct_button_width = (
            card_width - 30.0
        )
        direct_button_height = 42.0

        painter.setBrush(
            QBrush(
                QColor(
                    0,
                    95,
                    160,
                    245,
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255,
                ),
                2,
            )
        )

        painter.drawRoundedRect(
            QRectF(
                direct_button_x,
                direct_button_y,
                direct_button_width,
                direct_button_height,
            ),
            8.0,
            8.0,
        )

        font.setPointSize(13)
        font.setBold(True)
        painter.setFont(font)

        painter.drawText(
            QRectF(
                direct_button_x,
                direct_button_y,
                direct_button_width,
                direct_button_height,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "DIRECT TO",
        )

        self.direct_to_button_rect = QRectF(
            direct_button_x,
            direct_button_y,
            direct_button_width,
            direct_button_height,
        )

        if self.direct_to_state.active:
            cancel_button_x = (
                direct_button_x
            )
            cancel_button_y = (
                direct_button_y
                + direct_button_height
                + 8.0
            )
            cancel_button_width = (
                direct_button_width
            )
            cancel_button_height = 40.0

            painter.setBrush(
                QBrush(
                    QColor(
                        110,
                        35,
                        35,
                        245,
                    )
                )
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        255,
                        255,
                    ),
                    2,
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    cancel_button_x,
                    cancel_button_y,
                    cancel_button_width,
                    cancel_button_height,
                ),
                8.0,
                8.0,
            )

            painter.drawText(
                QRectF(
                    cancel_button_x,
                    cancel_button_y,
                    cancel_button_width,
                    cancel_button_height,
                ),
                Qt.AlignmentFlag.AlignCenter,
                "CANCEL DTO",
            )

            self.cancel_direct_to_button_rect = (
                QRectF(
                    cancel_button_x,
                    cancel_button_y,
                    cancel_button_width,
                    cancel_button_height,
                )
            )

        else:
            self.cancel_direct_to_button_rect = (
                QRectF()
            )

        painter.restore()
        
    def draw_touch_navigation(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        self.touch_navigation_state = (
            self.touch_navigation.layout(
                screen_width=width,
                screen_height=height,
                current_page=(
                    self.page_manager.current()
                ),
            )
        )

        painter.save()

        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)

        for button in (
            self.touch_navigation_state.buttons
        ):
            if button.selected:
                fill_color = QColor(
                    0,
                    110,
                    165,
                    240,
                )
            else:
                fill_color = QColor(
                    35,
                    35,
                    45,
                    235,
                )

            painter.setBrush(
                QBrush(
                    fill_color
                )
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        255,
                        255,
                    ),
                    2,
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    button.bounds.x,
                    button.bounds.y,
                    button.bounds.width,
                    button.bounds.height,
                ),
                8.0,
                8.0,
            )

            painter.drawText(
                QRectF(
                    button.bounds.x,
                    button.bounds.y,
                    button.bounds.width,
                    button.bounds.height,
                ),
                Qt.AlignmentFlag.AlignCenter,
                button.label,
            )

        painter.restore()
        
    def draw_guidance_touch_controls(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        button_width = 150.0
        button_height = 52.0
        margin = 16.0

        button_x = (
            width
            - button_width
            - margin
        )

        button_y = (
            height
            - button_height
            - margin
        )

        painter.save()

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255,
                ),
                2,
            )
        )

        painter.setBrush(
            QBrush(
                QColor(
                    35,
                    35,
                    45,
                    230,
                )
            )
        )

        painter.drawRoundedRect(
            QRectF(
                button_x,
                button_y,
                button_width,
                button_height,
            ),
            8.0,
            8.0,
        )

        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)

        painter.drawText(
            QRectF(
                button_x,
                button_y,
                button_width,
                button_height,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "GUIDANCE",
        )

        if not self.touch_guidance_menu_state.visible:
            painter.restore()
            return

        for button in (
            self.touch_guidance_menu_state.buttons
        ):
            if button.enabled:
                fill_color = QColor(
                    0,
                    125,
                    80,
                    235,
                )
                state_text = "ON"
            else:
                fill_color = QColor(
                    70,
                    70,
                    80,
                    235,
                )
                state_text = "OFF"

            painter.setBrush(
                QBrush(
                    fill_color
                )
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        255,
                        255,
                    ),
                    2,
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    button.bounds.x,
                    button.bounds.y,
                    button.bounds.width,
                    button.bounds.height,
                ),
                10.0,
                10.0,
            )

            font.setPointSize(13)
            font.setBold(True)
            painter.setFont(font)

            painter.drawText(
                QRectF(
                    button.bounds.x + 16.0,
                    button.bounds.y,
                    button.bounds.width - 90.0,
                    button.bounds.height,
                ),
                Qt.AlignmentFlag.AlignVCenter,
                button.label,
            )

            painter.drawText(
                QRectF(
                    button.bounds.x
                    + button.bounds.width
                    - 70.0,
                    button.bounds.y,
                    55.0,
                    button.bounds.height,
                ),
                (
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignRight
                ),
                state_text,
            )
            
        if (
            self.map_orientation_state.mode
            == "TRACK_UP"
        ):
            orientation_text = "TRK UP"
        else:
            orientation_text = "NORTH UP"

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)

        painter.drawText(
            QRectF(
                width - 170.0,
                55.0,
                150.0,
                28.0,
            ),
            (
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            ),
            orientation_text,
        )

        painter.restore()
    
    def draw_warning_strip(self, painter: QPainter, width: int) -> None:
        self.warning_manager.draw(painter, width)

    def paintEvent(self, event) -> None:  # noqa: N802, ARG002
        # event parameter required by Qt but unused in this implementation
        del event

        if self.pfd is None:
            return

        if self.page_renderer.draw_page():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        features = self.config.features
        declutter_level = self.config.declutter.level

        self.draw_background(painter, width, height)

        taxi_state = self.safe_taxi.update(self.pfd)
        if features.show_safe_taxi and taxi_state.active:
            self.draw_safe_taxi_map(painter, taxi_state, width, height)
            
            self.draw_touch_navigation(
                painter,
                width,
                height,
            )
            self.draw_warning_strip(painter, width)
            painter.end()
            return

        if (
            features.show_synthetic_vision
            and (
                self.guidance_touch_settings
                .synthetic_vision_enabled
            )
        ):
            self.draw_synthetic_vision(
                painter,
                self.pfd,
                width,
                height,
            )

        if features.show_attitude:
            self.draw_attitude(
                painter,
                self.pfd,
                width,
                height,
            )

            self.draw_hits_guidance(
                painter,
                width,
                height,
            )

            self.draw_flight_director(
                painter,
                width,
                height,
            )

        if (
            self.guidance_touch_settings
            .flight_path_marker_enabled
        ):
            self.draw_flight_path_marker(
                painter,
                width,
                height,
            )
        if features.show_airspeed:
            self.draw_airspeed_tape(painter, self.pfd, width, height)

        if features.show_altitude:
            self.draw_altitude_tape(painter, self.pfd, width, height)

        if features.show_vsi:
            self.draw_vsi(painter, self.pfd, width, height)

        if features.show_heading or features.show_hsi:
            self.draw_heading_strip(painter, self.pfd, width, height)

        if features.show_hsi:
            self.draw_hsi_compass_rose(painter, self.pfd, width, height)

        if features.show_turn_rate or features.show_slip_skid:
            self.draw_turn_and_slip(painter, self.pfd, width, height)

        if features.show_cdi or (features.show_vdi and self.config.vnav.enabled):
            self.draw_nav_cdi_vdi(painter, self.pfd, width, height)

        self.draw_top_data_bar(painter, self.pfd, width)
        self.draw_bottom_data_bar(painter, self.pfd, width, height)

        if declutter_level <= 0 and features.show_nearest_airports:
            self.draw_nearest_airports_overlay(painter, self.pfd, width, height)

        if declutter_level <= 0 and features.show_moving_map:
            map_state = self.moving_map.update(
                database=self.database,
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
                range_nm=self.map_range_nm,
            )
            self.draw_moving_map_overlay(painter, map_state, width, height)

        if declutter_level <= 0 and features.show_route:
            self.draw_route_overlay(painter, width, height)

        if declutter_level <= 0 and features.show_airport_info:
            self.draw_selected_airport_info(painter, width, height)

        if declutter_level <= 0:
            self.draw_waypoint_info_box(painter, self.pfd, width, height)
            self.draw_startup_status_box(painter, width, height)
            self.draw_sensor_status_panel(painter, width, height)
            self.draw_sim_profile_box(painter, width, height)

        if declutter_level <= 1:
            self.draw_navigation_status_box(painter, self.pfd, width, height)
            
        self.draw_direct_to_guidance_box(
            painter,
            width,
            height,
        )

        if declutter_level <= 1 and self.config.vnav.enabled:
            self.draw_vnav_info_box(painter, self.pfd, width, height)

        if features.show_terrain:
            terrain_state = self.terrain.update(
                aircraft_alt_ft=self.pfd.pressure_alt_ft,
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
            )
            self.draw_terrain_status_box(painter, terrain_state, width, height)
            self.draw_terrain_warning_banner(
                painter,
                width,
                height,
            )

        if features.show_obstacles:
            obstacle_state = self.obstacles.update(
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
                aircraft_alt_ft=self.pfd.pressure_alt_ft,
            )
            self.draw_obstacle_overlay(painter, obstacle_state, width, height)

        if features.show_traffic and self.config.stratux.enabled:
            self.draw_traffic_overlay(painter, self.stratux.read(), width, height)

        if features.show_weather:
            self.draw_weather_overlay(painter, self.weather.read(), width, height)
        self.draw_aircraft_state_label(
            painter,
            width,
            height,
        )

        self.draw_emergency_landing_guidance(
            painter,
            width,
            height,
        )

        self.draw_guidance_touch_controls(
            painter,
            width,
            height,
        )
        
        self.draw_sensor_watchdog_banner(
            painter,
            width,
            height,
        )
        
    def draw_sensor_watchdog_banner(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        state = self.sensor_watchdog_state

        if (
            not state.failed
            and not state.degraded
        ):
            return

        banner_width = 420.0
        banner_height = 52.0

        banner_x = (
            (width - banner_width)
            / 2.0
        )

        banner_y = 82.0

        if state.failed:
            background_color = QColor(
                180,
                0,
                0,
                235,
            )
        else:
            background_color = QColor(
                190,
                120,
                0,
                235,
            )

        painter.save()

        painter.setBrush(
            QBrush(
                background_color
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255,
                ),
                2,
            )
        )

        painter.drawRoundedRect(
            QRectF(
                banner_x,
                banner_y,
                banner_width,
                banner_height,
            ),
            8.0,
            8.0,
        )

        font = painter.font()
        font.setBold(True)
        font.setPointSize(15)
        painter.setFont(font)

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        painter.drawText(
            QRectF(
                banner_x,
                banner_y,
                banner_width,
                banner_height,
            ),
            Qt.AlignmentFlag.AlignCenter,
            state.message,
        )

        painter.restore()

    def draw_background(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(5, 5, 8))

    def draw_declutter_level_0_overlays(self, painter: QPainter, width: int, height: int, features) -> None:
        # Draw overlays that are shown only when declutter level is 0
        if features.show_nearest_airports:
            self.draw_nearest_airports_overlay(painter, self.pfd, width, height)

        if features.show_moving_map:
            map_state = self.moving_map.update(
                database=self.database,
                aircraft_lat=39.1031,
                aircraft_lon=-84.5120,
                range_nm=self.map_range_nm,
            )
            self.draw_moving_map_overlay(painter, map_state, width, height)

        if features.show_route:
            self.draw_route_overlay(painter, width, height)

        if features.show_airport_info:
            self.draw_selected_airport_info(painter, width, height)

        # Always draw these when declutter level is 0
        self.draw_waypoint_info_box(painter, self.pfd, width, height)
        self.draw_startup_status_box(painter, width, height)
        self.draw_sensor_status_panel(painter, width, height)
        self.draw_sim_profile_box(painter, width, height)

    def draw_synthetic_vision(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        scene = self.synthetic_vision.update(pfd)
        center_x = width // 2
        center_y = height // 2

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(-getattr(pfd, "roll_deg", 0.0))

        painter.fillRect(-width, -height * 2, width * 2, height * 2, QColor(*scene.sky_color))
        painter.fillRect(-width, 0, width * 2, height * 2, QColor(*scene.ground_color))

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(-width, 0, width, 0)
        painter.restore()

        for obj in scene.objects or []:
            x, y = project_object_to_screen(
                obj.rel_bearing_deg,
                obj.elevation_angle_deg,
                width,
                height,
                obj.distance_nm,
            )

            if not (0 <= x <= width and 0 <= y <= height):
                continue

            if obj.kind == "runway":
                runway_w = int(120 * obj.size)
                runway_h = int(35 * obj.size)

                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.setBrush(QBrush(QColor(40, 40, 40)))
                painter.drawRect(x - runway_w // 2, y - runway_h // 2, runway_w, runway_h)

                painter.setPen(QPen(QColor(255, 255, 0), 2))
                painter.drawLine(x, y - runway_h // 2, x, y + runway_h // 2)

                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x - 20, y - runway_h // 2 - 8, obj.label)
            else:
                box_w = int(70 * obj.size)
                box_h = int(38 * obj.size)

                painter.setPen(QPen(QColor(0, 255, 0), 3))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(x - box_w // 2, y - box_h // 2, box_w, box_h)

                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.drawText(x - 20, y - box_h // 2 - 8, obj.label)

    def draw_attitude(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height // 2
        horizon_width = int(width * 0.58)
        horizon_height = int(height * 0.70)

        roll_deg = getattr(pfd, "roll_deg", 0.0)
        pitch_deg = getattr(pfd, "pitch_deg", 0.0)

        painter.save()
        painter.setClipRect(
            center_x - horizon_width // 2,
            center_y - horizon_height // 2,
            horizon_width,
            horizon_height,
        )

        painter.translate(center_x, center_y)
        painter.rotate(-roll_deg)
        painter.translate(0, pitch_deg * 7.0)

        painter.fillRect(-horizon_width, -horizon_height * 2, horizon_width * 2, horizon_height * 2, QColor(25, 95, 180))
        painter.fillRect(-horizon_width, 0, horizon_width * 2, horizon_height * 2, QColor(125, 70, 25))

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(-horizon_width, 0, horizon_width, 0)

        self.draw_pitch_ladder(painter)
        painter.restore()

        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.drawRect(
            center_x - horizon_width // 2,
            center_y - horizon_height // 2,
            horizon_width,
            horizon_height,
        )

        painter.setPen(QPen(QColor(255, 220, 0), 4))
        painter.drawLine(center_x - 90, center_y, center_x - 25, center_y)
        painter.drawLine(center_x + 25, center_y, center_x + 90, center_y)
        painter.drawLine(center_x, center_y - 8, center_x, center_y + 8)

        self.draw_roll_scale(painter, center_x, center_y, horizon_height)

    def draw_pitch_ladder(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        for pitch in range(-30, 35, 5):
            if pitch == 0:
                continue

            y = -pitch * 7.0
            line_half = 55 if pitch % 10 == 0 else 35
            painter.drawLine(int(-line_half), int(y), int(line_half), int(y))

            if pitch % 10 == 0:
                label = str(abs(pitch))
                painter.drawText(int(-line_half - 38), int(y + 5), label)
                painter.drawText(int(line_half + 12), int(y + 5), label)

    def draw_roll_scale(self, painter: QPainter, center_x: int, center_y: int, horizon_height: int) -> None:
        radius = int(horizon_height * 0.40)
        painter.setPen(QPen(QColor(255, 255, 255), 2))

        for deg in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            angle = radians(deg - 90)
            outer_x = center_x + int(radius * cos(angle))
            outer_y = center_y + int(radius * sin(angle))
            inner = radius - (18 if deg in [-60, -30, 0, 30, 60] else 10)
            inner_x = center_x + int(inner * cos(angle))
            inner_y = center_y + int(inner * sin(angle))
            painter.drawLine(inner_x, inner_y, outer_x, outer_y)

    def draw_airspeed_tape(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        tape_x, tape_y, tape_w = 30, 95, 105
        tape_h = height - 190
        center_y = tape_y + tape_h // 2
        ias = pfd.ias_kt

        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(20, 20, 25))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        for speed in range(int(ias - 50), int(ias + 55), 10):
            y = center_y - int((speed - ias) * 4.0)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(tape_x + tape_w - 35, y, tape_x + tape_w - 5, y)
                painter.drawText(tape_x + 10, y + 5, str(speed))

        painter.fillRect(tape_x + 5, center_y - 25, tape_w - 10, 50, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(tape_x + 5, center_y - 25, tape_w - 10, 50)
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(
            QRectF(tape_x + 5, center_y - 25, tape_w - 10, 50),
            Qt.AlignmentFlag.AlignCenter,
            f"{ias:.0f}",
        )

    def draw_altitude_tape(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        tape_w = 120
        tape_x = width - tape_w - 30
        tape_y = 95
        tape_h = height - 190
        center_y = tape_y + tape_h // 2
        alt = pfd.pressure_alt_ft

        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(20, 20, 25))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        start_alt = int((alt - 1000) // 100) * 100
        end_alt = int((alt + 1100) // 100) * 100

        for altitude in range(start_alt, end_alt, 100):
            y = center_y - int(((altitude - alt) / 100.0) * 22.0)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(tape_x + 5, y, tape_x + 35, y)
                painter.drawText(tape_x + 42, y + 5, str(altitude))

        painter.fillRect(tape_x + 5, center_y - 25, tape_w - 10, 50, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(tape_x + 5, center_y - 25, tape_w - 10, 50)
        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        painter.drawText(
            QRectF(tape_x + 5, center_y - 25, tape_w - 10, 50),
            Qt.AlignmentFlag.AlignCenter,
            f"{alt:.0f}",
        )

    def draw_vsi(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        x = width - 180
        y = 120
        h = height - 240
        center_y = y + h // 2

        painter.setPen(
            QPen(
                QColor(
                    200,
                    200,
                    200,
                ),
                2,
            )
        )

        painter.drawLine(
            x,
            y,
            x,
            y + h,
        )

        clamped_vsi = max(
            -2000.0,
            min(
                2000.0,
                pfd.vsi_fpm,
            ),
        )

        pointer_y = center_y - int(
            (
                clamped_vsi
                / 2000.0
            )
            * (
                h
                / 2
            )
        )

        painter.setBrush(
            QBrush(
                QColor(
                    0,
                    255,
                    255,
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    0,
                    255,
                    255,
                ),
                2,
            )
        )

        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(
                        x - 18,
                        pointer_y,
                    ),
                    QPointF(
                        x - 38,
                        pointer_y - 10,
                    ),
                    QPointF(
                        x - 38,
                        pointer_y + 10,
                    ),
                ]
            )
        )
    def draw_heading_strip(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        strip_w = 500
        strip_h = 70
        strip_x = width // 2 - strip_w // 2
        strip_y = height - 95
        center_x = strip_x + strip_w // 2
        pixels_per_deg = 5.0

        heading = pfd.heading_deg

        if (
            self.direct_to_guidance_state.active
            and self.direct_to_guidance_state.bearing_deg
            is not None
        ):
            desired_track = (
                self.direct_to_guidance_state
                .bearing_deg
            )
            bearing = (
                self.direct_to_guidance_state
                .bearing_deg
            )
        else:
            desired_track = (
                pfd.desired_track_deg
            )
            bearing = (
                pfd.bearing_deg
            )

        painter.fillRect(strip_x, strip_y, strip_w, strip_h, QColor(15, 15, 20))
        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.drawRect(strip_x, strip_y, strip_w, strip_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        for hdg in range(int(heading - 50), int(heading + 55), 10):
            normalized = hdg % 360
            x = center_x + int((hdg - heading) * pixels_per_deg)
            if strip_x < x < strip_x + strip_w:
                painter.drawLine(x, strip_y + 5, x, strip_y + 25)
                painter.drawText(
                    x - 18,
                    strip_y + 50,
                    f"{normalized // 10:02d}",
                )

        self.draw_heading_pointer(painter, center_x, strip_y)
        self.draw_bearing_pointer(painter, bearing, heading, center_x, strip_x, strip_y, strip_w, strip_h, pixels_per_deg)
        self.draw_desired_track_pointer(painter, desired_track, heading, center_x, strip_x, strip_y, strip_w, pixels_per_deg)

    def draw_heading_pointer(self, painter: QPainter, center_x: int, strip_y: int) -> None:
        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawPolygon(
            QPolygonF([
                QPointF(center_x, strip_y + 5),
                QPointF(center_x - 10, strip_y + 25),
                QPointF(center_x + 10, strip_y + 25),
            ])
        )

    def draw_bearing_pointer(
        self,
        painter: QPainter,
        bearing: float,
        heading: float,
        center_x: int,
        strip_x: int,
        strip_y: int,
        strip_w: int,
        strip_h: int,
        pixels_per_deg: float,
    ) -> None:
        bearing_error = (bearing - heading + 180.0) % 360.0 - 180.0
        bearing_x = center_x + int(bearing_error * pixels_per_deg)

        if strip_x <= bearing_x <= strip_x + strip_w:
            painter.setBrush(QBrush(QColor(255, 0, 255)))
            painter.setPen(QPen(QColor(255, 0, 255), 2))
            painter.drawPolygon(
                QPolygonF([
                    QPointF(bearing_x, strip_y + strip_h - 5),
                    QPointF(bearing_x - 10, strip_y + strip_h - 25),
                    QPointF(bearing_x + 10, strip_y + strip_h - 25),
                ])
            )
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(bearing_x - 18, strip_y + strip_h - 30, "BRG")

    def draw_desired_track_pointer(
        self,
        painter: QPainter,
        desired_track: float,
        heading: float,
        center_x: int,
        strip_x: int,
        strip_y: int,
        strip_w: int,
        pixels_per_deg: float,
    ) -> None:
        dtk_error = (desired_track - heading + 180.0) % 360.0 - 180.0
        dtk_x = center_x + int(dtk_error * pixels_per_deg)

        if strip_x <= dtk_x <= strip_x + strip_w:
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawPolygon(
                QPolygonF([
                    QPointF(dtk_x, strip_y + 5),
                    QPointF(dtk_x - 10, strip_y + 25),
                    QPointF(dtk_x + 10, strip_y + 25),
                ])
            )
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(dtk_x - 16, strip_y + 38, "DTK")

    def draw_hsi_compass_rose(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height - 170
        radius = 95

        heading = pfd.heading_deg
        desired_track = pfd.desired_track_deg
        bearing = pfd.bearing_deg

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        for deg in range(0, 360, 30):
            relative = (deg - heading + 360) % 360
            angle = radians(relative - 90)

            outer_x = center_x + int(cos(angle) * radius)
            outer_y = center_y + int(sin(angle) * radius)
            inner_x = center_x + int(cos(angle) * (radius - 10))
            inner_y = center_y + int(sin(angle) * (radius - 10))

            painter.drawLine(inner_x, inner_y, outer_x, outer_y)

            label_x = center_x + int(cos(angle) * (radius - 25))
            label_y = center_y + int(sin(angle) * (radius - 25))

            painter.drawText(label_x - 10, label_y + 5, f"{deg // 10:02d}")

        dtk_relative = (desired_track - heading + 360) % 360
        dtk_angle = radians(dtk_relative - 90)

        if (
            self.direct_to_lateral_guidance_state.active
        ):
            displayed_cdi = (
                self.direct_to_lateral_guidance_state
                .lateral_error
            )
        else:
            displayed_cdi = (
                pfd.cdi
            )

        cdi_offset = (
            max(
                -1.0,
                min(
                    1.0,
                    displayed_cdi,
                ),
            )
            * 35
        )
        offset_angle = dtk_angle + radians(90)
        offset_x = int(cos(offset_angle) * cdi_offset)
        offset_y = int(sin(offset_angle) * cdi_offset)

        painter.setPen(QPen(QColor(0, 255, 0), 3))
        painter.drawLine(
            center_x + offset_x,
            center_y + offset_y,
            center_x + offset_x + int(cos(dtk_angle) * radius),
            center_y + offset_y + int(sin(dtk_angle) * radius),
        )
        painter.drawLine(
            center_x + offset_x,
            center_y + offset_y,
            center_x + offset_x - int(cos(dtk_angle) * radius),
            center_y + offset_y - int(sin(dtk_angle) * radius),
        )

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for dot in [-2, -1, 1, 2]:
            dot_x = center_x + int(cos(offset_angle) * dot * 18)
            dot_y = center_y + int(sin(offset_angle) * dot * 18)
            painter.drawEllipse(dot_x - 3, dot_y - 3, 6, 6)

        brg_relative = (bearing - heading + 360) % 360
        brg_angle = radians(brg_relative - 90)

        painter.setPen(QPen(QColor(255, 0, 255), 3))
        painter.drawLine(
            center_x,
            center_y,
            center_x + int(cos(brg_angle) * (radius - 15)),
            center_y + int(sin(brg_angle) * (radius - 15)),
        )

        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawPolygon(
            QPolygonF([
                QPointF(center_x, center_y - 12),
                QPointF(center_x - 8, center_y + 10),
                QPointF(center_x + 8, center_y + 10),
            ])
        )

        if self.config.obs.enabled:
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(center_x - 38, center_y + radius + 22, f"OBS {self.config.obs.selected_course_deg:.0f}°")

    def draw_turn_and_slip(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        y = 78

        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(center_x - 120, y, center_x + 120, y)
        painter.drawLine(center_x - 80, y - 8, center_x - 80, y + 8)
        painter.drawLine(center_x + 80, y - 8, center_x + 80, y + 8)

        ratio = max(-1.5, min(1.5, pfd.turn_rate_deg_sec / 3.0))
        pointer_x = center_x + int(ratio * 80)

        painter.setBrush(QBrush(QColor(255, 220, 0)))
        painter.setPen(QPen(QColor(255, 220, 0), 2))
        painter.drawEllipse(pointer_x - 7, y - 7, 14, 14)

        ball_y = y + 45
        ball_x = center_x + int(pfd.slip_skid * 70)

        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.drawLine(center_x - 80, ball_y, center_x + 80, ball_y)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(ball_x - 10, ball_y - 10, 20, 20)

    def draw_nav_cdi_vdi(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        features = self.config.features
        center_x = width // 2
        center_y = height // 2

        if features.show_cdi:
            cdi_y = center_y + 185
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(center_x - 125, cdi_y, center_x + 125, cdi_y)

            if (
                self.direct_to_lateral_guidance_state.active
            ):
                displayed_cdi = (
                    self.direct_to_lateral_guidance_state
                    .lateral_error
                )
            else:
                displayed_cdi = (
                    pfd.cdi
                )

            cdi_x = center_x + int(
                max(
                    -1.0,
                    min(
                        1.0,
                        displayed_cdi,
                    ),
                )
                * 100
            )
            painter.setBrush(QBrush(QColor(255, 0, 255)))
            painter.setPen(QPen(QColor(255, 0, 255), 2))
            painter.drawRect(cdi_x - 6, cdi_y - 28, 12, 56)

        if features.show_vdi and self.config.vnav.enabled:
            vdi_x = center_x + 290
            vdi_y = center_y - int(max(-1.0, min(1.0, pfd.vdi)) * 90)

            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawPolygon(
                QPolygonF([
                    QPointF(vdi_x, vdi_y),
                    QPointF(vdi_x + 22, vdi_y - 12),
                    QPointF(vdi_x + 22, vdi_y + 12),
                ])
            )

    def draw_top_data_bar(self, painter: QPainter, pfd: FlightData, width: int) -> None:
        painter.fillRect(0, 0, width, 55, QColor(0, 0, 0))
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        parts = []

        if self.config.features.show_tas:
            parts.append(f"TAS {pfd.tas_kt:.0f} KT")
        if self.config.features.show_ground_speed:
            parts.append(f"GS {pfd.ground_speed_kt:.0f} KT")
        if self.config.features.show_wind:
            parts.append(f"WIND {pfd.wind_direction_deg:.0f}°/{pfd.wind_speed_kt:.0f} KT")

        painter.drawText(QRectF(0, 0, width, 55), Qt.AlignmentFlag.AlignCenter, "    ".join(parts))

    def draw_bottom_data_bar(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        painter.fillRect(
            0,
            height - 35,
            width,
            35,
            QColor(0, 0, 0),
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Weight.Bold,
            )
        )

        if (
            self.direct_to_lateral_guidance_state.active
        ):
            displayed_cdi = (
                self.direct_to_lateral_guidance_state
                .lateral_error
            )
            cdi_source = "DTO"
        else:
            displayed_cdi = (
                pfd.cdi
            )
            cdi_source = "NAV"
            
        if (
            self.direct_to_guidance_state.active
            and self.direct_to_guidance_state.bearing_deg
            is not None
        ):
            displayed_bearing = (
                self.direct_to_guidance_state
                .bearing_deg
            )
            displayed_desired_track = (
                self.direct_to_guidance_state
                .bearing_deg
            )
        else:
            displayed_bearing = (
                pfd.bearing_deg
            )
            displayed_desired_track = (
                pfd.desired_track_deg
            )
            
        parts = [
            f"TRK {pfd.track_deg:.0f}°",
            f"BRG {displayed_bearing:.0f}°",
            f"DTK {displayed_desired_track:.0f}°",
            (
                f"OBS "
                f"{self.config.obs.selected_course_deg:.0f}°"
                if self.config.obs.enabled
                else ""
            ),
            (
                f"{cdi_source} CDI "
                f"{displayed_cdi:+.2f}"
            ),
        ]

        parts = [
            part
            for part in parts
            if part
        ]

        if (
            self.config.features.show_vdi
            and self.config.vnav.enabled
        ):
            parts.append(
                f"VDI {pfd.vdi:+.2f}°"
            )

        painter.drawText(
            QRectF(
                0,
                height - 35,
                width,
                35,
            ),
            Qt.AlignmentFlag.AlignCenter,
            "    ".join(parts),
        )

    def draw_vnav_info_box(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        box_x = width - 250
        box_y = 265
        box_w = 220
        box_h = 105

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 25, "VNAV")
        painter.drawText(box_x + 10, box_y + 50, f"TGT ALT {pfd.glidepath_target_alt_ft:.0f}")
        painter.drawText(box_x + 10, box_y + 75, f"ALT ERR {pfd.glidepath_alt_error_ft:+.0f}")
        painter.drawText(box_x + 10, box_y + 100, f"GP {self.config.vnav.glidepath_angle_deg:.1f}°")

    def draw_waypoint_info_box(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        box_x = width // 2 - 120
        box_y = 60
        box_w = 240
        box_h = 85

        if self.direct_to_guidance_state.active:
            waypoint_id = (
                self.direct_to_guidance_state.identifier
                or ""
            )

            bearing_deg = (
                self.direct_to_guidance_state.bearing_deg
                if self.direct_to_guidance_state.bearing_deg
                is not None
                else 0.0
            )

            distance_nm = (
                self.direct_to_guidance_state.distance_nm
                if self.direct_to_guidance_state.distance_nm
                is not None
                else 0.0
            )

            course_error_deg = (
                self.direct_to_guidance_state.course_error_deg
                if self.direct_to_guidance_state.course_error_deg
                is not None
                else 0.0
            )
        else:
            waypoint_id = (
                self.config.navigation.selected_waypoint_id
            )

            bearing_deg = (
                pfd.bearing_deg
            )

            distance_nm = (
                pfd.distance_to_waypoint_nm
            )

            course_error_deg = (
                pfd.course_error_deg
            )

        painter.fillRect(
            box_x,
            box_y,
            box_w,
            box_h,
            QColor(0, 0, 0),
        )

        painter.setPen(
            QPen(
                QColor(255, 255, 255),
                2,
            )
        )

        painter.drawRect(
            box_x,
            box_y,
            box_w,
            box_h,
        )

        painter.setFont(
            QFont(
                "Arial",
                13,
                QFont.Weight.Bold,
            )
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        painter.drawText(
            box_x + 10,
            box_y + 25,
            f"WPT {waypoint_id}",
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Weight.Bold,
            )
        )

        painter.drawText(
            box_x + 10,
            box_y + 52,
            f"BRG {bearing_deg:.0f}°",
        )

        painter.drawText(
            box_x + 120,
            box_y + 52,
            f"DIS {distance_nm:.1f}NM",
        )

        painter.drawText(
            box_x + 10,
            box_y + 75,
            f"CRS ERR {course_error_deg:+.0f}°",
        )

    def draw_navigation_status_box(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        active_leg = (
            self.route_manager.get_active_leg()
        )

        box_x = width // 2 - 150
        box_y = 150
        box_w = 300
        box_h = 90

        if self.direct_to_guidance_state.active:
            waypoint_id = (
                self.direct_to_guidance_state.identifier
                or ""
            )

            bearing_deg = (
                self.direct_to_guidance_state.bearing_deg
                if self.direct_to_guidance_state.bearing_deg
                is not None
                else 0.0
            )

            desired_track_deg = (
                bearing_deg
            )

            distance_nm = (
                self.direct_to_guidance_state.distance_nm
                if self.direct_to_guidance_state.distance_nm
                is not None
                else 0.0
            )

            nav_title = (
                f"DIRECT TO {waypoint_id}"
            )
        else:
            waypoint_id = (
                self.config.navigation.selected_waypoint_id
            )

            bearing_deg = (
                pfd.bearing_deg
            )

            desired_track_deg = (
                pfd.desired_track_deg
            )

            distance_nm = (
                pfd.distance_to_waypoint_nm
            )

            if active_leg is not None:
                nav_title = (
                    f"ACTIVE LEG "
                    f"{active_leg.from_ident} → "
                    f"{active_leg.to_ident}"
                )
            else:
                nav_title = (
                    f"DIRECT TO {waypoint_id}"
                )

        painter.fillRect(
            box_x,
            box_y,
            box_w,
            box_h,
            QColor(0, 0, 0),
        )

        painter.setPen(
            QPen(
                QColor(0, 255, 0),
                2,
            )
        )

        painter.drawRect(
            box_x,
            box_y,
            box_w,
            box_h,
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Weight.Bold,
            )
        )

        painter.setPen(
            QColor(
                0,
                255,
                0,
            )
        )

        painter.drawText(
            box_x + 10,
            box_y + 25,
            nav_title,
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        painter.drawText(
            box_x + 10,
            box_y + 52,
            f"DTK {desired_track_deg:.0f}°",
        )

        painter.drawText(
            box_x + 120,
            box_y + 52,
            f"BRG {bearing_deg:.0f}°",
        )

        painter.drawText(
            box_x + 10,
            box_y + 76,
            f"DIS {distance_nm:.1f} NM",
        )

    def draw_nearest_airports_overlay(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        nearest = self.database.nearest_airports(39.1031, -84.5120, max_results=5)

        box_x, box_y, box_w, box_h = 20, height - 210, 330, 165
        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        y = box_y + 28
        painter.drawText(box_x + 10, y, "NEAREST AIRPORTS")
        y += 25

        for distance_nm, airport in nearest:
            painter.drawText(box_x + 10, y, f"{airport.ident:<5} {distance_nm:>4.1f}NM {airport.name[:24]}")
            y += 22

    def draw_moving_map_overlay(
        self,
        painter: QPainter,
        map_state,
        width: int,
        height: int,
    ) -> None:
        box_x = 20
        box_y = 300
        box_w = 300
        box_h = 220

        painter.fillRect(
            box_x,
            box_y,
            box_w,
            box_h,
            QColor(0, 0, 0),
        )
        painter.setPen(
            QPen(
                QColor(0, 180, 255),
                2,
            )
        )
        painter.drawRect(
            box_x,
            box_y,
            box_w,
            box_h,
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Weight.Bold,
            )
        )
        painter.setPen(
            QColor(0, 180, 255)
        )
        painter.drawText(
            box_x + 10,
            box_y + 24,
            f"MAP {map_state.range_nm:.0f} NM",
        )

        center_x = box_x + box_w // 2
        center_y = box_y + box_h // 2

        radius = min(
            box_w,
            box_h,
        ) * 0.42

        painter.setPen(
            QPen(
                QColor(60, 60, 60),
                1,
            )
        )
        painter.drawEllipse(
            center_x - int(radius),
            center_y - int(radius),
            int(radius * 2),
            int(radius * 2),
        )

        emergency_plan = getattr(
            self,
            "emergency_landing_plan",
            None,
        )

        glide_range_nm = 0.0
        
        emergency_state = getattr(
            self,
            "emergency_airport_state",
            None,
        )
        
        track_deg = 0.0

        if self.pfd is not None:
            track_deg = (
                self.pfd.track_deg
            )

        self.map_orientation_state = (
            self.map_orientation
            .update_reference(
                track_deg=track_deg,
            )
        )

        if emergency_state is not None:
            result = getattr(
                emergency_state,
                "result",
                None,
            )

            if result is not None:
                glide_range_nm = max(
                    0.0,
                    float(
                        getattr(
                            result,
                            "glide_range_nm",
                            0.0,
                        )
                        or 0.0
                    ),
                )

        if (
            glide_range_nm > 0.0
            and map_state.range_nm > 0.0
        ):
            glide_radius = min(
                radius,
                radius
                * glide_range_nm
                / map_state.range_nm,
            )

            painter.setPen(
                QPen(
                    QColor(0, 255, 0),
                    2,
                )
            )
            painter.setBrush(
                QBrush(
                    Qt.BrushStyle.NoBrush
                )
            )
            painter.drawEllipse(
                center_x - int(glide_radius),
                center_y - int(glide_radius),
                int(glide_radius * 2),
                int(glide_radius * 2),
            )
            
        if (
            self.direct_to_state.active
            and self.direct_to_state.bearing_deg
            is not None
            and self.direct_to_state.distance_nm
            is not None
            and map_state.range_nm > 0.0
        ):
            dto_relative_bearing = (
                self.map_orientation
                .relative_bearing_deg(
                    bearing_deg=(
                        self.direct_to_state
                        .bearing_deg
                    ),
                )
            )

            if dto_relative_bearing is not None:
                dto_scale = min(
                    1.0,
                    (
                        self.direct_to_state
                        .distance_nm
                        / map_state.range_nm
                    ),
                )

                dto_angle = radians(
                    dto_relative_bearing
                    - 90.0
                )

                dto_x = center_x + int(
                    cos(dto_angle)
                    * radius
                    * dto_scale
                )

                dto_y = center_y + int(
                    sin(dto_angle)
                    * radius
                    * dto_scale
                )

                painter.setPen(
                    QPen(
                        QColor(
                            255,
                            0,
                            255,
                        ),
                        3,
                    )
                )

                painter.drawLine(
                    center_x,
                    center_y,
                    dto_x,
                    dto_y,
                )

                painter.setBrush(
                    QBrush(
                        QColor(
                            255,
                            0,
                            255,
                        )
                    )
                )

                painter.drawEllipse(
                    dto_x - 5,
                    dto_y - 5,
                    10,
                    10,
                )

        selected_airport = None

        if (
            emergency_plan is not None
            and emergency_plan.active
            and emergency_plan.airport_identifier
        ):
            selected_airport = (
                emergency_plan.airport_identifier.upper()
            )

        painter.setFont(
            QFont(
                "Arial",
                8,
                QFont.Weight.Bold,
            )
        )
        
        if (
            self.page_manager.current()
            == "MAP"
        ):
            self.map_airport_markers = []

        for airport in map_state.airports:
            if airport.distance_nm > map_state.range_nm:
                continue

            scale = (
                airport.distance_nm
                / map_state.range_nm
            )

            relative_bearing_deg = (
                self.map_orientation
                .relative_bearing_deg(
                    bearing_deg=(
                        airport.bearing_deg
                    ),
                )
            )

            if relative_bearing_deg is None:
                continue

            angle = radians(
                relative_bearing_deg
                - 90.0
            )

            airport_x = center_x + int(
                cos(angle)
                * radius
                * scale
            )
            airport_y = center_y + int(
                sin(angle)
                * radius
                * scale
            )
            
            if (
                self.page_manager.current()
                == "MAP"
            ):
                self.map_airport_markers.append(
                    MapAirportMarker(
                        identifier=airport.ident,
                        name=airport.name,
                        distance_nm=(
                            airport.distance_nm
                        ),
                        bearing_deg=(
                            airport.bearing_deg
                        ),
                        screen_x=(
                            airport_x
                            + self.map_viewport_state
                            .offset_x_px
                        ),
                        screen_y=(
                            airport_y
                            + self.map_viewport_state
                            .offset_y_px
                        ),
                    )
                )

            is_selected = (
                selected_airport is not None
                and airport.ident.upper()
                == selected_airport
            )
            
            is_touch_selected = (
                self.map_airport_selection.selected
                and (
                    self.map_airport_selection
                    .identifier
                    == airport.ident.upper()
                )
            )

            is_reachable = (
                glide_range_nm > 0.0
                and airport.distance_nm
                <= glide_range_nm
            )

            if is_selected:
                airport_color = QColor(
                    255,
                    0,
                    0,
                )
            elif is_touch_selected:
                airport_color = QColor(
                    0,
                    220,
                    255,
                )
            elif is_reachable:
                airport_color = QColor(
                    0,
                    255,
                    0,
                )
            else:
                airport_color = QColor(
                    130,
                    130,
                    130,
                )
                
            if is_touch_selected:
                painter.setPen(
                    QPen(
                        QColor(
                            0,
                            220,
                            255,
                        ),
                        3,
                    )
                )

                painter.setBrush(
                    QBrush(
                        Qt.BrushStyle.NoBrush
                    )
                )

                painter.drawEllipse(
                    airport_x - 11,
                    airport_y - 11,
                    22,
                    22,
                )

            if is_selected:
                painter.setPen(
                    QPen(
                        QColor(255, 0, 255),
                        3,
                    )
                )
                painter.drawLine(
                    center_x,
                    center_y,
                    airport_x,
                    airport_y,
                )

                painter.setPen(
                    QPen(
                        airport_color,
                        3,
                    )
                )
                painter.setBrush(
                    QBrush(
                        Qt.BrushStyle.NoBrush
                    )
                )
                painter.drawEllipse(
                    airport_x - 8,
                    airport_y - 8,
                    16,
                    16,
                )

            painter.setPen(
                QPen(
                    airport_color,
                    2,
                )
            )
            painter.setBrush(
                QBrush(
                    airport_color
                )
            )
            painter.drawEllipse(
                airport_x - 3,
                airport_y - 3,
                6,
                6,
            )

            painter.drawText(
                airport_x + 6,
                airport_y,
                airport.ident,
            )

        painter.setBrush(
            QBrush(
                QColor(255, 220, 0)
            )
        )
        painter.setPen(
            QPen(
                QColor(255, 220, 0),
                2,
            )
        )
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(
                        center_x,
                        center_y - 12,
                    ),
                    QPointF(
                        center_x - 8,
                        center_y + 10,
                    ),
                    QPointF(
                        center_x + 8,
                        center_y + 10,
                    ),
                ]
            )
        )
        
        if self.direct_to_guidance_state.active:
            guidance_ident = (
                self.direct_to_guidance_state
                .identifier
                or ""
            )

            course_error_deg = (
                self.direct_to_guidance_state
                .course_error_deg
            )

            if course_error_deg is None:
                course_error_deg = 0.0

            if abs(course_error_deg) < 1.0:
                correction_text = "ON COURSE"
            elif course_error_deg > 0.0:
                correction_text = (
                    f"TURN RIGHT "
                    f"{abs(course_error_deg):.0f}°"
                )
            else:
                correction_text = (
                    f"TURN LEFT "
                    f"{abs(course_error_deg):.0f}°"
                )

            painter.setFont(
                QFont(
                    "Arial",
                    9,
                    QFont.Weight.Bold,
                )
            )

            painter.setPen(
                QColor(
                    255,
                    0,
                    255,
                )
            )

            painter.drawText(
                box_x + 10,
                box_y + box_h - 30,
                (
                    f"DTO {guidance_ident}  "
                    f"{correction_text}"
                ),
            )

        if (
            emergency_plan is not None
            and emergency_plan.active
        ):
            painter.setFont(
                QFont(
                    "Arial",
                    9,
                    QFont.Weight.Bold,
                )
            )
            painter.setPen(
                QColor(255, 180, 0)
            )
            painter.drawText(
                box_x + 10,
                box_y + box_h - 8,
                (
                    f"GLIDE {glide_range_nm:.1f} NM"
                ),
            )
    def draw_route_overlay(self, painter: QPainter, width: int, height: int) -> None:
        route = self.route_manager.load_route()
        active_leg = self.route_manager.get_active_leg()

        box_x, box_y, box_w, box_h = width - 360, 120, 340, 135
        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 25, f"ROUTE: {route.get('route_id', 'NO ROUTE')}")
        painter.drawText(box_x + 10, box_y + 55, " → ".join(route.get("waypoints", []))[:35])

        if active_leg:
            painter.drawText(box_x + 10, box_y + 85, f"LEG: {active_leg.from_ident} → {active_leg.to_ident}")
            painter.drawText(box_x + 10, box_y + 112, f"DTK: {active_leg.desired_track_deg:.0f}°")

    def draw_selected_airport_info(self, painter: QPainter, width: int, height: int) -> None:
        airport_id = self.config.navigation.selected_waypoint_id
        airport = self.database.get_airport(airport_id)

        if airport is None:
            return

        runway = self.database.best_runway(airport_id)
        freqs = self.database.get_frequencies(airport_id)

        box_x = width - 360
        box_y = height - 350
        box_w = 340
        box_h = 300

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(box_x + 10, box_y + 25, f"{airport.ident} - {airport.name[:26]}")
        painter.drawText(box_x + 10, box_y + 55, f"Elev: {airport.elevation_ft:.0f} ft")

        if runway:
            painter.drawText(box_x + 10, box_y + 85, f"RWY {runway.le_ident}/{runway.he_ident}")
            painter.drawText(box_x + 10, box_y + 110, f"{runway.length_ft:.0f} x {runway.width_ft:.0f} ft {runway.surface[:10]}")

        y = box_y + 145
        for freq in freqs[:5]:
            painter.drawText(box_x + 10, y, f"{freq.type}: {freq.frequency_mhz:.3f}")
            y += 22

    def draw_startup_status_box(self, painter: QPainter, width: int, height: int) -> None:
        status = self.startup_status

        box_x = 20
        box_y = 20
        box_w = 280
        box_h = 65

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))

        color = QColor(0, 255, 0) if status.database_ok and status.config_ok else QColor(255, 0, 0)

        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 24, status.status_text)

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 50, f"APT {status.airports_loaded}  NAV {status.navaids_loaded}")

    def draw_sensor_status_panel(self, painter: QPainter, width: int, height: int) -> None:
        box_x = 310
        box_y = 20
        box_w = 300
        box_h = 90

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        mode_text = "HARDWARE" if self.use_hardware else "SIM"
        painter.setPen(QColor(0, 255, 0) if self.use_hardware else QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 24, f"SENSOR MODE: {mode_text}")

        if not self.use_hardware:
            painter.setPen(QColor(0, 180, 255))
            painter.drawText(box_x + 10, box_y + 52, "SIM DATA ACTIVE")
            return

        status = getattr(self.sensors, "status", None)

        if status is None:
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(box_x + 10, box_y + 52, "NO SENSOR STATUS")
            return

        def ok_text(
            label: str,
            ok: bool,
        ) -> str:
            return (
                f"{label}:"
                f"{'OK' if ok else 'OFF'}"
            )

        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )
        painter.drawText(
            box_x + 10,
            box_y + 52,
            "  ".join([
                ok_text("AHRS", status.bno085_ok),
                ok_text("BARO", status.baro_ok),
                ok_text("IAS", status.airspeed_ok),
            ]),
        )
        painter.drawText(box_x + 10, box_y + 76, ok_text("GPS", status.gps_ok))

    def draw_sim_profile_box(self, painter: QPainter, width: int, height: int) -> None:
        if self.use_hardware:
            return

        profile = self.config.simulation.profile.upper()

        box_x = 620
        box_y = 20
        box_w = 230
        box_h = 65

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 25, "SIM PROFILE")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 50, profile)

    def draw_terrain_status_box(self, painter: QPainter, terrain_state, width: int, height: int) -> None:
        box_x = 20
        box_y = 95
        box_w = 230
        box_h = 90

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))

        if terrain_state.warning_level == "red":
            color = QColor(255, 0, 0)
        elif terrain_state.warning_level == "yellow":
            color = QColor(255, 220, 0)
        else:
            color = QColor(0, 255, 0)

        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(color)
        source_label = (
            "SRTM"
            if self.real_terrain_enabled
            else "FALLBACK"
        )

        painter.drawText(
            box_x + 10,
            box_y + 25,
            f"TERRAIN [{source_label}]",
        )

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 52, f"ELEV {terrain_state.terrain_elevation_ft:.0f} FT")
        painter.drawText(box_x + 10, box_y + 76, f"CLR {terrain_state.clearance_ft:.0f} FT")

    def draw_terrain_alert(self, painter: QPainter, terrain_state, width: int, height: int) -> None:
        if terrain_state.warning_level == "none":
            return

        color = QColor(255, 0, 0) if terrain_state.warning_level == "red" else QColor(255, 220, 0)

        painter.setPen(QPen(color, 3))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 55, width, 40), Qt.AlignmentFlag.AlignCenter, f"TERRAIN {terrain_state.clearance_ft:.0f} FT")

    def draw_obstacle_overlay(self, painter: QPainter, obstacle_state, width: int, height: int) -> None:
        if not obstacle_state.nearby:
            return

        box_x = 20
        box_y = 195
        box_w = 260
        box_h = 90

        color = QColor(255, 0, 0) if obstacle_state.warning else QColor(255, 220, 0)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 25, "OBSTACLE")

        obstacle = obstacle_state.nearby[0]

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 52, f"{obstacle.ident}")
        painter.drawText(box_x + 10, box_y + 76, f"{obstacle.distance_nm:.1f}NM BRG {obstacle.bearing_deg:.0f}°")

    def draw_safe_taxi_map(self, painter: QPainter, taxi_state, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(15, 15, 15))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(30, 45, f"SAFE TAXI - {taxi_state.airport_id}")

    def draw_traffic_overlay(self, painter: QPainter, stratux_state, width: int, height: int) -> None:
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 255, 255) if stratux_state.ok else QColor(255, 180, 0))
        painter.drawText(width - 230, 80, "STRATUX ONLINE" if stratux_state.ok else "STRATUX OFFLINE")

    def draw_weather_overlay(self, painter: QPainter, weather_state, width: int, height: int) -> None:
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 255, 0) if weather_state.ok else QColor(255, 180, 0))
        painter.drawText(width - 230, 105, "WX ONLINE" if weather_state.ok else "WX WAITING")
        
    def draw_emergency_landing_guidance(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        plan = getattr(
            self,
            "emergency_landing_plan",
            None,
        )

        if plan is None or not plan.active:
            return

        box_w = 500
        box_h = 170
        box_x = width // 2 - box_w // 2
        box_y = 65

        painter.fillRect(
            box_x,
            box_y,
            box_w,
            box_h,
            QColor(0, 0, 0),
        )

        border_color = (
            QColor(255, 0, 0)
            if not plan.valid
            else QColor(255, 180, 0)
        )

        painter.setPen(
            QPen(
                border_color,
                4,
            )
        )
        painter.drawRect(
            box_x,
            box_y,
            box_w,
            box_h,
        )

        painter.setFont(
            QFont(
                "Arial",
                18,
                QFont.Weight.Bold,
            )
        )
        painter.setPen(border_color)
        painter.drawText(
            box_x + 15,
            box_y + 30,
            "EMERGENCY LANDING",
        )

        painter.setFont(
            QFont(
                "Arial",
                13,
                QFont.Weight.Bold,
            )
        )
        painter.setPen(
            QColor(
                255,
                255,
                255,
            )
        )

        if not plan.valid:
            painter.drawText(
                box_x + 15,
                box_y + 65,
                plan.instruction,
            )

            if plan.recommended_speed_kt is not None:
                painter.drawText(
                    box_x + 15,
                    box_y + 100,
                    (
                        "BEST GLIDE "
                        f"{plan.recommended_speed_kt:.0f} KT"
                    ),
                )

            painter.drawText(
                box_x + 15,
                box_y + 135,
                (
                    "CHECKLIST: "
                    f"{plan.checklist_name}"
                ),
            )
            return

        airport = (
            plan.airport_identifier
            or "UNKNOWN"
        )

        distance_text = (
            f"{plan.distance_nm:.1f} NM"
            if plan.distance_nm is not None
            else "-- NM"
        )

        bearing_text = (
            f"{plan.bearing_deg:.0f}°"
            if plan.bearing_deg is not None
            else "--°"
        )

        painter.drawText(
            box_x + 15,
            box_y + 62,
            (
                f"DIVERT: {airport}    "
                f"DIST: {distance_text}    "
                f"BRG: {bearing_text}"
            ),
        )

        speed_text = (
            f"{plan.recommended_speed_kt:.0f} KT"
            if plan.recommended_speed_kt is not None
            else "-- KT"
        )

        time_text = "--:--"

        if plan.estimated_time_sec is not None:
            total_seconds = max(
                0,
                int(plan.estimated_time_sec),
            )
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            time_text = (
                f"{minutes:02d}:{seconds:02d}"
            )

        painter.drawText(
            box_x + 15,
            box_y + 95,
            (
                f"BEST GLIDE: {speed_text}    "
                f"TIME: {time_text}"
            ),
        )

        arrival_text = (
            f"{plan.arrival_altitude_ft:.0f} FT"
            if plan.arrival_altitude_ft is not None
            else "-- FT"
        )

        margin_text = (
            f"{plan.safety_margin_ft:.0f} FT"
            if plan.safety_margin_ft is not None
            else "-- FT"
        )

        painter.drawText(
            box_x + 15,
            box_y + 128,
            (
                f"ARRIVAL ALT: {arrival_text}    "
                f"MARGIN: {margin_text}"
            ),
        )

        painter.setPen(
            QColor(
                255,
                220,
                0,
            )
        )
        painter.drawText(
            box_x + 15,
            box_y + 158,
            plan.instruction,
        )
        
        
    
    def draw_aircraft_state_label(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        if not hasattr(self, "aircraft"):
            return
        engine_state = self.aircraft.engine_state
        engine_health = engine_state.health
        
        engine = engine_state.data
        engine_health = engine_state.health
        engine_analysis = engine_state.analysis
        engine_trend = engine_state.trend

        flight_state = self.aircraft.flight_state

        phase = flight_state.phase
        moving = "MOVING" if flight_state.aircraft_moving else "STOPPED"
        airborne = "AIRBORNE" if flight_state.airborne else "GROUND"

        box_w = 250
        box_h = 154
        box_x = width - box_w - 30
        box_y = 58

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(0, 0, 0))
        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 22, f"PHASE: {phase}")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 43, f"{moving} / {airborne}")
        painter.setPen(QColor(255, 255, 0))
        painter.drawText(
            box_x + 10,
            box_y + 64,
            f"CHECKLIST: {self.checklist_state.active}",
        )
        checklist_mode = (
            "SUPPRESSED"
            if getattr(self.checklist_state, "popup_suppressed", False)
            else "AUTO"
        )

        painter.setPen(QColor(255, 180, 0) if checklist_mode == "SUPPRESSED" else QColor(0, 255, 0))
        painter.drawText(
            box_x + 10,
            box_y + 84,
            f"CHECKLIST MODE: {checklist_mode}  U=CLR",
        )
        engine_health = self.aircraft.engine_state.health
        engine_score = engine_health.health_score
        engine_status = engine_health.status

        if engine_score >= 85:
            engine_color = QColor(0, 255, 0)
        elif engine_score >= 60:
            engine_color = QColor(255, 220, 0)
        else:
            engine_color = QColor(255, 0, 0)

        painter.setPen(engine_color)
        painter.drawText(
            box_x + 10,
            box_y + 104,
            f"ENGINE: {engine_score}% {engine_status}",
        )
        recommendation = getattr(self, "aircraft_recommendation", None)

        if recommendation is not None:
            severity = getattr(recommendation, "severity", "NORMAL")
            title = getattr(recommendation, "title", "Normal")
            action = getattr(recommendation, "recommendation", "")
            
        urgency_s = getattr(recommendation, "urgency_s", None)

        urgency_text = ""
        if urgency_s is not None:
            urgency_text = f" {urgency_s:.0f}s"
            
        confidence = getattr(recommendation, "confidence", None)

        confidence_text = ""
        if confidence is not None:
            confidence_text = f" {confidence * 100:.0f}%"

        if severity == "CAUTION":
            rec_color = QColor(255, 220, 0)
        elif severity in {"WARNING", "CRITICAL"}:
            rec_color = QColor(255, 0, 0)
        else:
            rec_color = QColor(0, 255, 0)

        painter.setPen(rec_color)
        painter.drawText(
            box_x + 10,
            box_y + 124,
            f"AI: {title} [{severity}]{urgency_text}{confidence_text}",
        )

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            box_x + 10,
            box_y + 144,
            action[:28],
        )

    def point(x: float, y: float) -> QPointF:
        return QPointF(float(x), float(y))


    def heading_label(heading: int) -> str:
        heading = heading % 360

        if heading == 0:
            return "N"
        if heading == 90:
            return "E"
        if heading == 180:
            return "S"
        if heading == 270:
            return "W"

        return f"{heading // 10:02d}"


    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Blake PFD visual demo")

        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument("--sim", action="store_true", help="Run using simulated sensor data")
        mode_group.add_argument("--hardware", action="store_true", help="Run using real hardware sensor readers")

        parser.add_argument("--replay-log", help="Replay a recorded flight log CSV")

        return parser.parse_args()


    def main() -> None:
        args = parse_args()

        app = QApplication(sys.argv)
        window = BlakePfdDemo(
            use_hardware=args.hardware,
            replay_log=args.replay_log,
        )
        window.show()
        sys.exit(app.exec())


    if __name__ == "__main__":
        main()
        
    def draw_direct_to_guidance_box(
            self,
            painter: QPainter,
            width: int,
            height: int,
        ) -> None:
            state = self.direct_to_guidance_state

            if not state.active:
                return

            box_w = 300
            box_h = 95
            box_x = width // 2 - box_w // 2
            box_y = 245

            painter.fillRect(
                box_x,
                box_y,
                box_w,
                box_h,
                QColor(
                    0,
                    0,
                    0,
                ),
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        0,
                        255,
                    ),
                    2,
                )
            )

            painter.drawRect(
                box_x,
                box_y,
                box_w,
                box_h,
            )

            painter.setFont(
                QFont(
                    "Arial",
                    12,
                    QFont.Weight.Bold,
                )
            )

            ident = (
                state.identifier
                or ""
            )

            bearing = (
                state.bearing_deg
                if state.bearing_deg is not None
                else 0.0
            )

            distance = (
                state.distance_nm
                if state.distance_nm is not None
                else 0.0
            )

            error = (
                state.course_error_deg
                if state.course_error_deg is not None
                else 0.0
            )

            painter.setPen(
                QColor(
                    255,
                    0,
                    255,
                )
            )

            painter.drawText(
                box_x + 10,
                box_y + 24,
                f"DTO {ident}",
            )

            painter.setPen(
                QColor(
                    255,
                    255,
                    255,
                )
            )

            painter.drawText(
                box_x + 10,
                box_y + 50,
                (
                    f"BRG {bearing:.0f}°   "
                    f"DIS {distance:.1f} NM"
                ),
            )

            if abs(error) < 1.0:
                correction_text = "ON COURSE"
            elif error > 0.0:
                correction_text = (
                    f"RIGHT {abs(error):.0f}°"
                )
            else:
                correction_text = (
                    f"LEFT {abs(error):.0f}°"
                )

            painter.setPen(
                QColor(
                    0,
                    255,
                    120,
                )
            )

            painter.drawText(
                box_x + 10,
                box_y + 76,
                correction_text,
            )
