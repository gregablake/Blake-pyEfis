from __future__ import annotations
from dataclasses import replace
import argparse
import os
import sys
from time import monotonic
from pathlib import Path
from math import cos, isfinite, radians, sin
from pathlib import Path

import yaml
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF, QLinearGradient
from PyQt6.QtWidgets import QApplication, QWidget

from pyefis.user.blake_pfd.airport_info_page import AirportInfoPage
from pyefis.user.blake_pfd.audio_alerts import AudioAlertManager
from pyefis.user.blake_pfd.config_loader import load_config
from pyefis.user.blake_pfd.core.page_manager import PageManager
from pyefis.user.blake_pfd.core.page_renderer import PageRenderer
from pyefis.user.blake_pfd.core.pfd_layout import PfdLayout
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
from pyefis.user.blake_pfd.obstacle_database import (
    ObstacleDatabase,
)
from pyefis.user.blake_pfd.obstacle_runtime import (
    ObstacleRuntimeProvider,
)
from pyefis.user.blake_pfd.obstacles import (
    ObstacleState,
)
from pyefis.user.blake_pfd.core.obstacle_projection import (
    ObstacleProjectionComputer,
)
from pyefis.user.blake_pfd.route_manager import RouteManager
from pyefis.user.blake_pfd.safe_taxi import SafeTaxiComputer
from pyefis.user.blake_pfd.sensors_sim import SimulatedSensorSource
from pyefis.user.blake_pfd.startup_check import run_startup_check
from pyefis.user.blake_pfd.stratux_reader import StratuxReader
from pyefis.user.blake_pfd.core.traffic_geometry import (
    calculate_traffic_geometry,
)
from pyefis.user.blake_pfd.synthetic_vision import (
    SyntheticVisionComputer,
    project_object_to_screen,
)
from pyefis.user.blake_pfd.terrain import TerrainComputer
from pyefis.user.blake_pfd.weather_reader import WeatherReader
from pyefis.user.blake_pfd.core.event_manager import EventManager
from pyefis.user.blake_pfd.core.flight_state_manager import FlightStateManager
from pyefis.user.blake_pfd.core.sensor_manager import (
    EngineDataUnavailableError,
    SensorManager,
)
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
from pyefis.user.blake_pfd.core.runway_geometry import (
    RunwayGeometryComputer,
)
from pyefis.user.blake_pfd.core.safe_taxi_ground_gate import SafeTaxiGroundGate
from pyefis.user.blake_pfd.core.safe_taxi_projection import (
    SafeTaxiMapProjector,
)
from pyefis.user.blake_pfd.core.safe_taxi_display_gate import (
    evaluate_safe_taxi_inputs,
    safe_taxi_takeover_allowed,
)

from pyefis.user.blake_pfd.core.runway_projection import (
    RunwayProjectionComputer,
)

from pyefis.user.blake_pfd.core.terrain_surface import (
    TerrainSurface,
    TerrainSurfaceGenerator,
)

from pyefis.user.blake_pfd.core.terrain_rebase import (
    TerrainSurfaceRebaser,
)

from pyefis.user.blake_pfd.core.terrain_projection import (
    TerrainProjectionComputer,
)

from pyefis.user.blake_pfd.core.terrain_visual_classifier import (
    TerrainVisualClassifier,
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

from pyefis.user.blake_pfd.core.touch_baro_setting import (
    TouchBaroSetting,
)

from pyefis.user.blake_pfd.core.baro_setting_store import (
    BaroSettingStore,
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

from pyefis.user.blake_pfd.core.data_freshness import (
    DataFreshnessMonitor,
)

from pyefis.user.blake_pfd.core.engine_sensor_monitor import (
    EngineSensorMonitor,
)
from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineSensorStatus,
)

from pyefis.user.blake_pfd.core.startup_gate import (
    StartupGate,
)

from pyefis.user.blake_pfd.core.reboot_recovery import (
    RebootRecovery,
)
from pyefis.user.blake_pfd.core.shutdown_marker import (
    ShutdownMarker,
)

from pyefis.user.blake_pfd.core.app_heartbeat import (
    AppHeartbeat,
)

from pyefis.user.blake_pfd.core.heartbeat_file import (
    HeartbeatFile,
)

from pyefis.user.blake_pfd.core.advisory_latch import (
    AdvisoryLatch,
)


class BlakePfdDemo(QWidget):
    def __init__(
        self,
        use_hardware: bool = False,
        replay_log: str | None = None,
        baro_state_path: str | Path | None = None,
    ) -> None:
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

        self.startup_gate = StartupGate()

        self.startup_gate_state = (
            self.startup_gate.evaluate(
                config_ok=(
                    self.startup_status.config_ok
                ),
                database_ok=(
                    self.startup_status.database_ok
                ),
                flight_data_available=False,
                attitude_valid=False,
                air_data_valid=False,
                hardware_mode=use_hardware,
            )
        )

        self.shutdown_marker = ShutdownMarker(
            Path.home()
            / ".local"
            / "state"
            / "blake_pyefis"
            / "shutdown.state"
        )

        self.previous_shutdown_clean = (
            self.shutdown_marker
            .previous_shutdown_clean()
        )

        self.shutdown_marker.mark_running()

        self.reboot_recovery = (
            RebootRecovery()
        )

        self.reboot_recovery_state = (
            self.reboot_recovery.evaluate(
                previous_shutdown_clean=(
                    self.previous_shutdown_clean
                ),
                startup_ready=(
                    self.startup_gate_state.ready
                ),
                flight_data_valid=False,
            )
        )

        self.app_heartbeat = AppHeartbeat(
            stall_after_s=2.0,
        )

        self.heartbeat_file = HeartbeatFile(
            Path(
                "/tmp/blake_pyefis/app.heartbeat"
            ),
            write_interval_s=0.5,
        )

        self.app_heartbeat_state = (
            self.app_heartbeat.evaluate(
                monotonic()
            )
        )

        self.sensor_watchdog = SensorWatchdog()

        self.sensor_fault_message = ""

        self.bno085_freshness_monitor = (
            DataFreshnessMonitor(
                stale_after_s=0.5,
            )
        )

        self.baro_freshness_monitor = (
            DataFreshnessMonitor(
                stale_after_s=1.0,
            )
        )

        self.airspeed_freshness_monitor = (
            DataFreshnessMonitor(
                stale_after_s=1.0,
            )
        )

        self.gps_freshness_monitor = (
            DataFreshnessMonitor(
                stale_after_s=2.5,
            )
        )

        self.engine_freshness_monitor = (
            DataFreshnessMonitor(
                stale_after_s=1.0,
            )
        )

        self.engine_freshness_state = (
            self.engine_freshness_monitor.evaluate(
                monotonic()
            )
        )

        self.engine_sensor_monitor = (
            EngineSensorMonitor()
        )
        self.engine_sensor_status = (
            EngineSensorStatus()
        )

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

        if baro_state_path is None:
            baro_state_path = (
                Path.home()
                / ".local"
                / "state"
                / "blake_pyefis"
                / "baro_setting.json"
            )

        self.baro_setting_store = (
            BaroSettingStore(
                baro_state_path
            )
        )

        self.baro_persistence_enabled = (
            replay_log is None
        )

        if self.baro_persistence_enabled:
            persisted_baro = (
                self.baro_setting_store.load(
                    default_inhg=(
                        self.flight_computer
                        .baro_setting_controller
                        .setting_inhg
                    )
                )
            )

            (
                self.flight_computer
                .baro_setting_controller
                .set_setting(
                    persisted_baro
                )
            )

        self.synthetic_vision = SyntheticVisionComputer()

        self.runway_geometry_computer = (
            RunwayGeometryComputer()
        )

        self.safe_taxi_projector = (
            SafeTaxiMapProjector(
                range_ft=3500.0,
            )
        )

        self.runway_projection_computer = (
            RunwayProjectionComputer()
        )

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

        self.touch_baro_setting = (
            TouchBaroSetting()
        )

        self.touch_baro_state = (
            self.touch_baro_setting.layout(
                screen_width=(
                    self.config.display.width
                ),
                screen_height=(
                    self.config.display.height
                ),
            )
        )

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

        self.safe_taxi = SafeTaxiComputer(
            database=self.database,
            config=self.config.safe_taxi,
        )

        self.safe_taxi_ground_gate = (
            SafeTaxiGroundGate()
        )

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

        self.synthetic_terrain_generator = (
            TerrainSurfaceGenerator(
                elevation_sampler=(
                    self.terrain_sampler
                ),
                # BLAKE_TERRAIN_MESH_DETAIL_V1
                # Higher-density visual mesh; use real sampled elevations.
                # Preserve the original footprint and near/far boundaries.
                # The separate terrain-alert/profile pipeline is unchanged.
                forward_distances_nm=(
                    0.125,
                    0.1875,
                    0.25,
                    0.375,
                    0.5,
                    0.625,
                    0.75,
                    1.0,
                    1.25,
                    1.5,
                    1.75,
                    2.0,
                    2.5,
                    3.0,
                    4.0,
                    5.0,
                    6.5,
                    8.0,
                    10.0,
                ),
                lateral_fractions=(
                    -1.0,
                    -0.8,
                    -0.6,
                    -0.4,
                    -0.2,
                    0.0,
                    0.2,
                    0.4,
                    0.6,
                    0.8,
                    1.0,
                ),
                half_width_ratio=0.75,
            )
        )

        # BLAKE_V6_MOUNTAIN_VISUAL_MESH: denser DISPLAY mesh only.
        # Existing SRTM sampler, projection and severity thresholds remain.
        # Only used in the explicitly selected non-hardware mountain scene.
        if (
            not use_hardware
            and os.environ.get("BLAKE_PFD_V6_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
        ):
            base_forward = self.synthetic_terrain_generator.forward_distances_nm
            extra_forward = (
                0.9, 1.125, 1.625, 2.25, 2.75,
                3.5, 4.5, 5.75, 7.25, 9.0,
            )
            # V8 ridge-only: extend the far field to 18 NM. All elevations
            # remain real SRTM samples; missing tiles create partial mesh,
            # never synthetic/fabricated hills. V7 mountain stays unchanged.
            v8_ridge_mesh = (
                os.environ.get("BLAKE_PFD_V8_RIDGE_DEMO") == "1"
                and os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
            )
            if v8_ridge_mesh:
                extra_forward += (5.5, 6.0, 7.0, 7.5, 8.5, 11.0, 12.0, 13.5, 15.0, 16.5, 18.0)
            # V10: only the opt-in stationary ridge view uses moderately
            # denser *real sampled* SRTM geometry. No height interpolation
            # or terrain warning thresholds are modified.
            v10_ridge_mesh = (
                v8_ridge_mesh
                and os.environ.get("BLAKE_PFD_V10_RIDGE_VISUALS") == "1"
            )
            if v10_ridge_mesh:
                extra_forward += (
                    1.375, 1.875, 2.375, 3.25,
                    4.25, 6.25, 9.5, 12.5,
                )
            self.synthetic_terrain_generator = TerrainSurfaceGenerator(
                elevation_sampler=self.terrain_sampler,
                forward_distances_nm=tuple(sorted(set(base_forward + extra_forward))),
                lateral_fractions=(
                    tuple(index / 10.0 for index in range(-10, 11))
                    if v10_ridge_mesh else
                    tuple(index / 8.0 for index in range(-8, 9))
                    if v8_ridge_mesh else
                    tuple(index / 6.0 for index in range(-6, 7))
                ),
                half_width_ratio=0.75,
            )

        self.synthetic_terrain_rebaser = (
            TerrainSurfaceRebaser()
        )

        self.synthetic_terrain_projection = (
            TerrainProjectionComputer()
        )

        self.synthetic_terrain_classifier = (
            TerrainVisualClassifier()
        )

        self.synthetic_terrain_surface = (
            TerrainSurface()
        )

        self.synthetic_terrain_last_refresh_s: (
            float | None
        ) = None

        self.synthetic_terrain_last_refresh_heading_deg: (
            float | None
        ) = None

        self.synthetic_terrain_refresh_interval_s = (
            1.0
        )

        self.synthetic_terrain_heading_refresh_threshold_deg = (
            10.0
        )

        self.synthetic_terrain_heading_min_refresh_interval_s = (
            0.20
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

        self.obstacles = (
            ObstacleRuntimeProvider(
                ObstacleDatabase(
                    self.config.synthetic_vision
                    .obstacle_database_path
                )
            )
        )

        self.obstacle_projection_computer = (
            ObstacleProjectionComputer()
        )

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
                flight_state=self.flight_state,
                pilot_selected=(
                    self.pilot_emergency_selected
                ),
                sensor_status=self.engine_sensor_status,
            )
        )
        self.checklist_manager = ChecklistManager()
        self.checklist_state = self.checklist_manager.state
        self.sensor_manager = SensorManager(
            flight_computer=self.flight_computer,
            use_hardware=use_hardware,
            replay_log=replay_log,
        )

        self.engine_data_available = False
        self.engine_fault_message = ""
        self.engine_data = None
        self.engine_state = None

        self.engine_manager = EngineManager()
        self.engine_trend_manager = EngineTrendManager()
        self.engine_analyzer = EngineAnalyzer()
        self.cylinder_analyzer = CylinderAnalyzer()
        self.engine_predictor = EnginePredictor()
        self.engine_advisor = EngineAdvisor()
        self.advisory_latch = AdvisoryLatch(
            activate_samples=3,
            clear_samples=5,
        )

        self.aircraft_recommendation = (
            self.aircraft_intelligence.analyze(
                self.aircraft
            )
        )

        if self.aircraft_recommendation.severity != "NORMAL":
            self.aircraft_recommendation = (
                type(self.aircraft_recommendation)()
            )

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

    def _automatic_checklist_popup_allowed(self) -> bool:
        """Disable only automatic checklist takeovers in V6 demo scenes.

        Manual navigation to the checklist and ordinary/hardware flight
        behavior remain unchanged. This is UI-only; no alert gate is altered.
        """
        return not (
            not self.use_hardware
            and os.environ.get("BLAKE_PFD_V6_VISUALS") == "1"
            and (
                os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
                or os.environ.get("BLAKE_PFD_SCENIC_DEMO") == "1"
            )
        )

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
        try:
            engine_data = (
                self.sensor_manager.read_engine()
            )
        except EngineDataUnavailableError:
            self.engine_data_available = False
            self.engine_fault_message = (
                "ENGINE DATA UNAVAILABLE"
            )
            self.engine_data = None
            self.engine_state = None
            self.engine_sensor_status = (
                EngineSensorStatus()
            )
            return

        source_timestamp_s = getattr(
            self.sensor_manager.engine_source,
            "last_success_s",
            None,
        )

        if source_timestamp_s is not None:
            self.engine_freshness_monitor.mark_update(
                source_timestamp_s
            )

        self.engine_freshness_state = (
            self.engine_freshness_monitor.evaluate(
                monotonic()
            )
        )

        self.engine_sensor_status = (
            self.engine_sensor_monitor.evaluate(
                engine_data,
                source_fresh=(
                    self.engine_freshness_state.fresh
                ),
            )
        )

        if self.engine_freshness_state.stale:
            self.engine_data_available = False
            self.engine_fault_message = (
                "EMS DATA STALE"
            )
            self.engine_data = None
            self.engine_state = None
            return

        self.engine_data_available = True
        self.engine_fault_message = ""
        self.engine_data = engine_data

        self.engine_health = self.engine_manager.update(
            self.engine_data,
            sensor_status=self.engine_sensor_status,
        )

        self.engine_trend = self.engine_trend_manager.update(
            self.engine_data,
            sensor_status=self.engine_sensor_status,
        )

        self.engine_analysis = self.engine_analyzer.analyze(
            self.engine_data,
            self.engine_health,
            self.engine_trend,
            sensor_status=self.engine_sensor_status,
        )

        self.cylinder_analysis = (
            self.cylinder_analyzer.analyze(
                self.engine_data,
                sensor_status=(
                    self.engine_sensor_status
                ),
            )
        )

        self.engine_prediction = (
            self.engine_predictor.predict(
                self.engine_trend
            )
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
            flight_state=getattr(
                self,
                "flight_state",
                None,
            ),
            sensor_status=self.engine_sensor_status,
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

    def refresh_synthetic_terrain(
        self,
        now_s: float,
    ) -> None:
        pfd = self.pfd

        watchdog = (
            self.sensor_watchdog_state
        )

        inputs_valid = (
            self.real_terrain_enabled
            and pfd is not None
            and pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
            and (
                self.terrain_startup_status
                .predictive_alerts_enabled
            )
        )

        if not inputs_valid:
            self.synthetic_terrain_surface = (
                TerrainSurface()
            )

            self.synthetic_terrain_last_refresh_s = (
                None
            )

            self.synthetic_terrain_last_refresh_heading_deg = (
                None
            )

            return

        try:
            current_heading = float(
                pfd.heading_deg
            )
        except (TypeError, ValueError):
            current_heading = float("nan")

        if not isfinite(current_heading):
            self.synthetic_terrain_surface = (
                TerrainSurface()
            )

            self.synthetic_terrain_last_refresh_s = (
                None
            )

            self.synthetic_terrain_last_refresh_heading_deg = (
                None
            )

            return

        current_heading = (
            current_heading % 360.0
        )

        last_refresh = (
            self.synthetic_terrain_last_refresh_s
        )

        last_heading = (
            self.synthetic_terrain_last_refresh_heading_deg
        )

        heading_refresh_due = False

        if last_heading is not None:
            heading_change_deg = abs(
                (
                    current_heading
                    - last_heading
                    + 180.0
                )
                % 360.0
                - 180.0
            )

            heading_refresh_due = (
                heading_change_deg
                >= (
                    self
                    .synthetic_terrain_heading_refresh_threshold_deg
                )
            )

        elapsed_s = (
            None
            if last_refresh is None
            else now_s - last_refresh
        )

        time_refresh_due = (
            elapsed_s is None
            or elapsed_s
            >= self.synthetic_terrain_refresh_interval_s
        )

        heading_refresh_allowed = (
            heading_refresh_due
            and elapsed_s is not None
            and elapsed_s
            >= (
                self
                .synthetic_terrain_heading_min_refresh_interval_s
            )
        )

        if (
            not time_refresh_due
            and not heading_refresh_allowed
        ):
            return

        # Record the attempt time and heading before
        # sampling. If terrain is unavailable, this
        # prevents repeated reads at the 20 Hz display
        # rate while still allowing the footprint to
        # follow a meaningful aircraft turn.
        self.synthetic_terrain_last_refresh_s = (
            now_s
        )

        self.synthetic_terrain_last_refresh_heading_deg = (
            current_heading
        )

        self.synthetic_terrain_surface = (
            self.synthetic_terrain_generator.generate(
                aircraft_lat_deg=(
                    pfd.latitude_deg
                ),
                aircraft_lon_deg=(
                    pfd.longitude_deg
                ),
                aircraft_alt_ft=(
                    pfd.indicated_alt_ft
                ),
                heading_deg=(
                    current_heading
                ),
            )
        )

    def update_data(self) -> None:
        heartbeat_now_s = monotonic()

        self.app_heartbeat.beat(
            heartbeat_now_s
        )

        try:
            self.heartbeat_file.maybe_write(
                heartbeat_now_s
            )
        except OSError:
            pass

        self.app_heartbeat_state = (
            self.app_heartbeat.evaluate(
                heartbeat_now_s
            )
        )


        self.pfd = self.sensor_manager.read_flight()
        self.update_engine_state()

        sensor_faults: list[str] = []

        if self.use_hardware:
            hardware_status = getattr(
                self.sensor_manager.flight_sensor_source,
                "status",
                None,
            )

            if hardware_status is not None:
                now_s = monotonic()

                if (
                    hardware_status.bno085_last_success_s
                    is not None
                ):
                    self.bno085_freshness.mark_update(
                        hardware_status
                        .bno085_last_success_s
                    )

                if (
                    hardware_status.baro_last_success_s
                    is not None
                ):
                    self.baro_freshness.mark_update(
                        hardware_status
                        .baro_last_success_s
                    )

                if (
                    hardware_status.airspeed_last_success_s
                    is not None
                ):
                    self.airspeed_freshness.mark_update(
                        hardware_status
                        .airspeed_last_success_s
                    )

                if (
                    hardware_status.gps_last_success_s
                    is not None
                ):
                    self.gps_freshness.mark_update(
                        hardware_status
                        .gps_last_success_s
                    )

                self.bno085_freshness_state = (
                    self.bno085_freshness.evaluate(
                        now_s
                    )
                )

                self.baro_freshness_state = (
                    self.baro_freshness.evaluate(
                        now_s
                    )
                )

                self.airspeed_freshness_state = (
                    self.airspeed_freshness.evaluate(
                        now_s
                    )
                )

                self.gps_freshness_state = (
                    self.gps_freshness.evaluate(
                        now_s
                    )
                )

                if not hardware_status.bno085_ok:
                    sensor_faults.append(
                        "AHRS FAIL"
                    )
                elif self.bno085_freshness_state.stale:
                    sensor_faults.append(
                        "AHRS DATA STALE"
                    )

                if not hardware_status.baro_ok:
                    sensor_faults.append(
                        "BARO FAIL"
                    )
                elif self.baro_freshness_state.stale:
                    sensor_faults.append(
                        "BARO DATA STALE"
                    )

                if not hardware_status.airspeed_ok:
                    sensor_faults.append(
                        "AIRSPEED FAIL"
                    )
                elif self.airspeed_freshness_state.stale:
                    sensor_faults.append(
                        "AIRSPEED DATA STALE"
                    )

                if not hardware_status.gps_ok:
                    sensor_faults.append(
                        "GPS FAIL"
                    )
                elif self.gps_freshness_state.stale:
                    sensor_faults.append(
                        "GPS DATA STALE"
                    )

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

                position_fresh = (
                    self.gps_freshness_state.fresh
                )

                attitude_fresh = (
                    self.bno085_freshness_state.fresh
                )

                air_data_fresh = (
                    self.baro_freshness_state.fresh
                    and self.airspeed_freshness_state.fresh
                )

            else:
                attitude_valid = False
                air_data_valid = False
                attitude_fresh = False
                air_data_fresh = False
                position_valid = False
                position_fresh = False

                sensor_faults.append(
                    "SENSOR STATUS LOST"
                )

        else:
            attitude_valid = True
            air_data_valid = True
            attitude_fresh = True
            air_data_fresh = True
            position_fresh = True

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
                position_fresh=position_fresh,
                attitude_valid=attitude_valid,
                air_data_valid=air_data_valid,
                attitude_fresh=attitude_fresh,
                air_data_fresh=air_data_fresh,
            )
        )

        self.startup_gate_state = (
            self.startup_gate.evaluate(
                config_ok=(
                    self.startup_status.config_ok
                ),
                database_ok=(
                    self.startup_status.database_ok
                ),
                flight_data_available=(
                    self.pfd is not None
                ),
                attitude_valid=attitude_valid,
                air_data_valid=air_data_valid,
                attitude_fresh=attitude_fresh,
                air_data_fresh=air_data_fresh,
                hardware_mode=self.use_hardware,
            )
        )

        self.reboot_recovery_state = (
            self.reboot_recovery.evaluate(
                previous_shutdown_clean=(
                    self.previous_shutdown_clean
                ),
                startup_ready=(
                    self.startup_gate_state.ready
                ),
                flight_data_valid=(
                    self.pfd is not None
                    and attitude_valid
                    and air_data_valid
                    and attitude_fresh
                    and air_data_fresh
                ),
            )
        )
        if sensor_faults:
            self.sensor_fault_message = (
                " / ".join(
                    sensor_faults
                )
            )
        else:
            self.sensor_fault_message = ""

        watchdog = self.sensor_watchdog_state

        # Navigation/geographic runtime consumers
        # must treat stale GPS exactly like invalid
        # GPS.  position_valid alone is not enough.
        runtime_position_usable = bool(
            self.pfd is not None
            and self.pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

        runtime_air_data_usable = bool(
            watchdog.air_data_valid
            and watchdog.air_data_fresh
        )

        runtime_terrain_inputs_usable = bool(
            runtime_position_usable
            and runtime_air_data_usable
        )

        engine = (
            self.engine_state.data
            if self.engine_state is not None
            else None
        )

        if self.pfd is not None:
            if engine is not None:
                engine.fuel_range_nm = (
                    engine.endurance_hr
                    * self.pfd.ground_speed_kt
                )

            self.flight_state = (
                self.flight_state_manager.update(
                    self.pfd,
                    engine=engine,
                    sensor_status=self.engine_sensor_status,
                )
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
                        runtime_position_usable
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
                    sensor_status=(
                        self.engine_sensor_status
                    ),
                )
            )

        if (
            self.direct_to_state.active
            and runtime_position_usable
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

        if runtime_position_usable:
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
                        runtime_position_usable
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
            if runtime_terrain_inputs_usable:
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
                            self.pfd.indicated_alt_ft
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

            if runtime_terrain_inputs_usable:
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
                            self.pfd.indicated_alt_ft
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
                runtime_terrain_inputs_usable
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
                            self.pfd.indicated_alt_ft
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
                        self.pfd.indicated_alt_ft
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

            if (
                self.checklist_state.should_popup
                and self._automatic_checklist_popup_allowed()
            ):
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
                    sensor_status=self.engine_sensor_status,
                )
            )

        self.refresh_synthetic_terrain(
            heartbeat_now_s
        )

        raw_recommendation = (
            self.aircraft_intelligence.analyze(
                self.aircraft
            )
        )

        if raw_recommendation.severity == "NORMAL":
            latch_key = None
        else:
            latch_key = raw_recommendation.title

        latch_state = self.advisory_latch.update(
            latch_key,
            raw_recommendation.severity,
        )

        if latch_state.active_key is None:
            # Only return to NORMAL after the latch has
            # satisfied its clear-sample requirement.
            if raw_recommendation.severity == "NORMAL":
                self.aircraft_recommendation = (
                    raw_recommendation
                )

        elif (
            latch_state.active_key
            == raw_recommendation.title
            and latch_state.active_severity
            == raw_recommendation.severity
        ):
            # The current raw recommendation is now
            # officially latched and may be displayed.
            self.aircraft_recommendation = (
                raw_recommendation
            )

        # Otherwise keep displaying the previously
        # latched recommendation while a replacement
        # or clear condition is still being confirmed.

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

        if engine is not None:
            self.ems_alert_history.update(
                engine,
                sensor_status=self.engine_sensor_status,
            )
            self.ems_trend_page.add_sample(
                engine,
                sensor_status=self.engine_sensor_status,
            )

            self.audio_alerts.update(
                engine,
                silenced=(
                    self.ems_alert_history.silenced
                ),
                sensor_status=self.engine_sensor_status,
            )
        else:
            self.ems_trend_page.set_data_available(
                False,
                message=(
                    self.engine_fault_message
                    or "EMS DATA UNAVAILABLE"
                ),
            )
            self.audio_alerts.reset()

        if (
            self.config.logging.enabled
            and self.pfd is not None
            and engine is not None
        ):
            self.flight_logger.maybe_log(
                self.pfd,
                waypoint_id=(
                    self.config.navigation.selected_waypoint_id
                ),
                engine=engine,
                sensor_status=(
                    self.engine_sensor_status
                ),
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
                    and self.pfd.position_valid
                    and (
                        self.sensor_watchdog_state
                        .position_valid
                    )
                    and (
                        self.sensor_watchdog_state
                        .position_fresh
                    )
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

            self.touch_baro_state = (
                self.touch_baro_setting.layout(
                    screen_width=self.width(),
                    screen_height=self.height(),
                )
            )

            baro_action = (
                self.touch_baro_setting
                .action_for_touch(
                    point_x=touch_x,
                    point_y=touch_y,
                )
            )

            if baro_action == "increment":
                new_baro_setting = (
                    self.flight_computer
                    .baro_setting_controller
                    .increment()
                )

                if self.baro_persistence_enabled:
                    try:
                        self.baro_setting_store.save(
                            new_baro_setting
                        )
                    except OSError:
                        self.baro_persistence_enabled = False

                self.update()
                event.accept()
                return

            if baro_action == "decrement":
                new_baro_setting = (
                    self.flight_computer
                    .baro_setting_controller
                    .decrement()
                )

                if self.baro_persistence_enabled:
                    try:
                        self.baro_setting_store.save(
                            new_baro_setting
                        )
                    except OSError:
                        self.baro_persistence_enabled = False

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

    def closeEvent(
        self,
        event,
    ) -> None:  # noqa: N802
        if self.timer.isActive():
            self.timer.stop()

        try:
            self.shutdown_marker.mark_clean_shutdown()
        except OSError:
            pass
        try:
            self.heartbeat_file.remove()
        except OSError:
            pass

        super().closeEvent(
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
        if getattr(self, "_v14_cincinnati_profile_enabled", lambda: False)():
            self._v15_log_warning_transition(presentation)

        if not presentation.visible:
            return

        if presentation.priority == "CRITICAL":
            color = QColor(220, 0, 0)

        elif presentation.priority == "WARNING":
            color = QColor(190, 30, 30)

        else:
            color = QColor(255, 180, 0)

        if self._v12_ridge_visuals() or self._v13_cincinnati_diagnostics_enabled():
            # Red/orange warning remains full-width and equally prominent.
            # Only the positions and text size change in the opt-in ridge demo.
            painter.save()
            painter.fillRect(0, 0, width, 72, color)
            title_rect, message_rect, detail_rect = (
                self._v13_cincinnati_warning_rects(width)
                if self._v13_cincinnati_diagnostics_enabled()
                else self._v12_warning_text_rects(width)
            )
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("DejaVu Sans", 17, QFont.Weight.Bold))
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                presentation.title,
            )
            painter.setFont(QFont("DejaVu Sans", 15, QFont.Weight.Bold))
            painter.drawText(
                message_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                presentation.message,
            )
            if presentation.detail:
                painter.setFont(QFont("DejaVu Sans", 9))
                painter.drawText(
                    detail_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    presentation.detail,
                )
            painter.restore()
            return

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

            if self._v10_ridge_visuals():
                # V10: preserve exact warning wording and priority, but
                # fit the secondary detail before the altitude tape.
                font.setPointSize(9)
                painter.setFont(font)
                painter.drawText(
                    QRectF(width * 0.31, 37, width * 0.35, 28),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    presentation.detail,
                )
            else:
                painter.drawText(
                    width - 250,
                    55,
                    presentation.detail,
                )

    # VISUAL_REFINEMENT_20261008
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

        # Fewer, smaller, low-opacity HITS gates keep the pitch ladder legible.
        for box in reversed(
            state.boxes[-3:]
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
                * width * 0.50
            )

            box_height = (
                box.height_fraction
                * height * 0.50
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
                1.25
                - box.depth_fraction
                * 0.35
            )

            opacity = int(
                84
                - box.depth_fraction
                * 44
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

        horizontal_bar_half_width = 40.0
        vertical_bar_half_height = 32.0
        center_gap = 13.0

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
                3,
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

        v14_paint_start = (
            monotonic() if self._v14_cincinnati_profile_enabled() else None
        )
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        layout = PfdLayout.build(
            width,
            height,
        )

        features = self.config.features
        declutter_level = self.config.declutter.level

        # Never replay threats from an earlier frame or stale position.
        self._visible_obstacle_threats = []
        self.draw_background(painter, width, height)

        flight_state = getattr(
            getattr(
                self,
                "aircraft",
                None,
            ),
            "flight_state",
            None,
        )

        safe_taxi_safety = (
            evaluate_safe_taxi_inputs(
                watchdog=(
                    self.sensor_watchdog_state
                ),
                flight_state=flight_state,
            )
        )

        watchdog = self.sensor_watchdog_state

        # Geographic overlays must never silently
        # fall back to a fixed/demo aircraft
        # position.  Only current, validated GPS
        # position is usable.
        position_usable = bool(
            self.pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

        safe_taxi_inputs_fresh = bool(
            watchdog.position_valid
            and watchdog.position_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        )

        ground_state = (
            self.safe_taxi_ground_gate.update(
                flight=self.pfd,
                flight_state=flight_state,
                inputs_fresh=(
                    safe_taxi_inputs_fresh
                ),
                now_s=monotonic(),
            )
        )

        taxi_state = self.safe_taxi.update(
            self.pfd,
            position_fresh=(
                safe_taxi_safety.position_fresh
            ),
            airborne=(
                safe_taxi_safety.airborne_inhibit
                or not ground_state.confirmed
            ),
        )

        if safe_taxi_takeover_allowed(
            feature_enabled=(
                features.show_safe_taxi
            ),
            auto_switch_enabled=(
                self.config.safe_taxi
                .auto_switch_enabled
            ),
            taxi_active=(
                taxi_state.active
                and ground_state.confirmed
            ),
            safety=safe_taxi_safety,
        ):
            self.draw_safe_taxi_map(painter, taxi_state, width, height)

            self.draw_touch_navigation(
                painter,
                width,
                height,
            )
            self.draw_warning_strip(painter, width)
            painter.end()
            self._v14_record_paint(v14_paint_start, monotonic())
            return

        if (
            features.show_attitude
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
        ):
            self.draw_attitude(
                painter,
                self.pfd,
                width,
                height,
            )

        obstacle_state = None

        if features.show_obstacles:
            obstacle_inputs_fresh = bool(
                self.pfd.position_valid
                and watchdog.position_valid
                and watchdog.position_fresh
                and watchdog.air_data_valid
                and watchdog.air_data_fresh
            )

            if obstacle_inputs_fresh:
                obstacle_state = (
                    self.obstacles.update(
                        aircraft_lat=(
                            self.pfd.latitude_deg
                        ),
                        aircraft_lon=(
                            self.pfd.longitude_deg
                        ),
                        aircraft_alt_ft=(
                            self.pfd.indicated_alt_ft
                        ),
                    )
                )
            else:
                obstacle_state = (
                    ObstacleState(
                        ok=False,
                        nearby=[],
                        warning=False,
                    )
                )

        if (
            features.show_synthetic_vision
            and (
                self.guidance_touch_settings
                .synthetic_vision_enabled
            )
            and position_usable
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            self.draw_synthetic_vision(
                painter,
                self.pfd,
                width,
                height,
                obstacle_state=(
                    obstacle_state
                ),
            )

        if (
            features.show_attitude
            and position_usable
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            painter.save()

            painter.translate(
                layout.flight_view.x,
                layout.flight_view.y,
            )

            painter.setClipRect(
                0,
                0,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            # Keep HITS outside the airspeed/altitude tapes and HSI.
            # The original validated navigation gate remains unchanged.
            painter.save()
            painter.setClipRect(
                QRectF(
                    100, 36,
                    max(0, layout.flight_view.width - 200),
                    max(0, layout.flight_view.height * 0.53),
                ),
                Qt.ClipOperation.IntersectClip,
            )
            if not self._v8_ridge_scene():
                self.draw_hits_guidance(
                    painter,
                    layout.flight_view.width,
                    layout.flight_view.height,
                )
            painter.restore()

            if not self._v8_ridge_scene():
                self.draw_flight_director(
                    painter,
                    layout.flight_view.width,
                    layout.flight_view.height,
                )

            painter.restore()

        if (
            self.guidance_touch_settings
            .flight_path_marker_enabled
            and not self._v8_ridge_scene()
            and position_usable
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            painter.save()

            painter.translate(
                layout.flight_view.x,
                layout.flight_view.y,
            )

            painter.setClipRect(
                0,
                0,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            self.draw_flight_path_marker(
                painter,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            painter.restore()
        if (
            features.show_airspeed
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            painter.save()

            painter.translate(
                layout.flight_view.x,
                layout.flight_view.y,
            )

            painter.setClipRect(
                0,
                0,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            self.draw_airspeed_tape(
                painter,
                self.pfd,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            painter.restore()

        if (
            features.show_altitude
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            painter.save()

            painter.translate(
                layout.flight_view.x,
                layout.flight_view.y,
            )

            painter.setClipRect(
                0,
                0,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            self.draw_altitude_tape(
                painter,
                self.pfd,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            painter.restore()

        if (
            features.show_vsi
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            self.draw_vsi(painter, self.pfd, width, height)

        if (
            (features.show_heading or features.show_hsi)
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
        ):
            # GARMIN REDESIGN: legacy horizontal heading strip disabled.
            pass

        if (
            features.show_hsi
            and position_usable
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
        ):
            painter.save()

            painter.translate(
                layout.flight_view.x,
                layout.flight_view.y,
            )

            painter.setClipRect(
                0,
                0,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            self.draw_hsi_compass_rose(
                painter,
                self.pfd,
                layout.flight_view.width,
                layout.flight_view.height,
            )

            painter.restore()

        if (
            (features.show_turn_rate or features.show_slip_skid)
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
        ):
            painter.save()
            painter.translate(
                layout.flight_view.x,
                layout.flight_view.y,
            )
            self.draw_turn_and_slip(
                painter,
                self.pfd,
                layout.flight_view.width,
                layout.flight_view.height,
            )
            painter.restore()

        # V9: an explicitly route-free static camera has no CDI/VDI command.
        if (
            not self._v8_ridge_scene()
            and (features.show_cdi or (features.show_vdi and self.config.vnav.enabled))
        ):
            self.draw_nav_cdi_vdi(painter, self.pfd, width, height)

        self.draw_top_data_bar(painter, self.pfd, width)
        # GARMIN REDESIGN: legacy bottom navigation strip disabled.

        if declutter_level <= 0 and features.show_nearest_airports:
            self.draw_nearest_airports_overlay(painter, self.pfd, width, height)

        if (
            declutter_level <= 0
            and features.show_moving_map
            and position_usable
        ):
            map_state = self.moving_map.update(
                database=self.database,
                aircraft_lat=self.pfd.latitude_deg,
                aircraft_lon=self.pfd.longitude_deg,
                range_nm=self.map_range_nm,
            )
            painter.save()
            painter.setClipRect(5, 350, 170, 215)
            self.draw_moving_map_overlay(
                painter,
                map_state,
                width,
                height,
            )
            painter.restore()

        # GARMIN REDESIGN:
        # Legacy waypoint/status/direct-to/VNAV boxes were drawn over the
        # synthetic-vision and HSI area. Their underlying navigation state
        # remains active; presentation will move to the Garmin-style
        # top/right information areas.

        if features.show_terrain:
            terrain_inputs_usable = bool(
                position_usable
                and watchdog.air_data_valid
                and watchdog.air_data_fresh
            )

            if terrain_inputs_usable:
                terrain_state = self.terrain.update(
                    aircraft_alt_ft=(
                        self.pfd.indicated_alt_ft
                    ),
                    aircraft_lat=(
                        self.pfd.latitude_deg
                    ),
                    aircraft_lon=(
                        self.pfd.longitude_deg
                    ),
                )

                self.draw_terrain_status_box(
                    painter,
                    terrain_state,
                    width,
                    height,
                )

            self.draw_terrain_warning_banner(
                painter,
                width,
                height,
            )

        if (
            features.show_obstacles
            and obstacle_state is not None
        ):
            self.draw_obstacle_overlay(
                painter,
                obstacle_state,
                width,
                height,
            )

        stratux_state = None
        weather_state = None

        # Read Stratux only once per paint cycle.
        #
        # Weather is intentionally drawn before
        # traffic so future NEXRAD graphics remain
        # underneath traffic targets.
        if (
            self.config.stratux.enabled
            and (
                features.show_traffic
                or features.show_weather
            )
        ):
            (
                stratux_state,
                weather_state,
            ) = self._read_stratux_weather_states()

        if features.show_weather:
            if weather_state is None:
                weather_state = self.weather.read()

            painter.save()
            painter.setClipRect(5, 372, 170, 193)
            self.draw_weather_overlay(
                painter,
                weather_state,
                width,
                height,
            )
            painter.restore()

        if (
            features.show_traffic
            and self.config.stratux.enabled
            and stratux_state is not None
        ):
            painter.save()
            painter.setClipRect(5, 372, 170, 193)
            self.draw_traffic_overlay(
                painter,
                stratux_state,
                width,
                height,
            )
            painter.restore()
        self.draw_aircraft_state_label(
            painter,
            width,
            height,
        )

        self.draw_compact_engine_overlay(
            painter,
            x=layout.left_panel.x + 10,
            y=layout.left_panel.y + 10,
            width=layout.left_panel.width - 20,
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

        # VISUAL_CLEANUP_20261009: Paint opaque right information panels
        # AFTER the other noncritical graphic overlays. This prevents
        # later geometry/labels from bleeding through those panels.
        # Validated obstacle threats and safety banners remain ABOVE them.
        if declutter_level <= 0 and (features.show_route or features.show_airport_info):
            painter.fillRect(width - 6, 48, 6, 275, QColor(8, 12, 20, 255))
        if declutter_level <= 0 and features.show_route:
            self.draw_route_overlay(painter, width, height)
        if declutter_level <= 0 and features.show_airport_info:
            self.draw_selected_airport_info(painter, width, height)

        # Ensure verified RED synthetic-vision threats remain visible
        # even where the HSI or other panels overlap their symbols.
        # Sensor-failure/reboot/startup banners are drawn afterward.
        # V13: developer overlay is always UNDER higher-priority red threats.
        self.draw_v13_cincinnati_diagnostics(painter, width)
        self.draw_priority_obstacle_threats(painter, width, height)

        self.draw_sensor_watchdog_banner(
            painter,
            width,
            height,
        )

        self.draw_reboot_recovery_banner(
            painter,
            width,
            height,
        )

        self.draw_startup_gate_banner(
            painter,
            width,
            height,
        )
        # Last drawing operation: measured rate is shown one frame later.
        if v14_paint_start is not None:
            self._v14_record_paint(v14_paint_start, monotonic())

    def draw_reboot_recovery_banner(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        state = self.reboot_recovery_state

        if not state.inhibit_ready:
            return

        banner_width = 520.0
        banner_height = 52.0

        banner_x = (
            (width - banner_width)
            / 2.0
        )

        banner_y = 140.0

        painter.save()

        painter.setBrush(
            QBrush(
                QColor(
                    170,
                    45,
                    0,
                    240,
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
        font.setPointSize(14)
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

    def draw_startup_gate_banner(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        state = self.startup_gate_state

        if state.ready:
            return

        banner_width = 520.0
        banner_height = 60.0

        banner_x = (
            (width - banner_width)
            / 2.0
        )

        banner_y = 18.0

        if state.blocked:
            background_color = QColor(
                190,
                0,
                0,
                245,
            )
        else:
            background_color = QColor(
                180,
                110,
                0,
                245,
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
                3,
            )
        )

        painter.drawRoundedRect(
            QRectF(
                banner_x,
                banner_y,
                banner_width,
                banner_height,
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
            (
                self.sensor_fault_message
                or state.message
            ),
        )

        painter.restore()

    def draw_background(self, painter: QPainter, width: int, height: int) -> None:
        painter.fillRect(0, 0, width, height, QColor(5, 5, 8))

    def draw_declutter_level_0_overlays(self, painter: QPainter, width: int, height: int, features) -> None:
        # Draw overlays that are shown only when declutter level is 0
        watchdog = self.sensor_watchdog_state

        position_usable = bool(
            self.pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

        if features.show_nearest_airports:
            self.draw_nearest_airports_overlay(
                painter,
                self.pfd,
                width,
                height,
            )

        if (
            features.show_moving_map
            and position_usable
        ):
            map_state = self.moving_map.update(
                database=self.database,
                aircraft_lat=self.pfd.latitude_deg,
                aircraft_lon=self.pfd.longitude_deg,
                range_nm=self.map_range_nm,
            )
            self.draw_moving_map_overlay(
                painter,
                map_state,
                width,
                height,
            )

        if features.show_route:
            self.draw_route_overlay(painter, width, height)

        if features.show_airport_info:
            self.draw_selected_airport_info(painter, width, height)

        # GARMIN REDESIGN: legacy center/status boxes intentionally omitted.
    def draw_synthetic_runway(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        watchdog = self.sensor_watchdog_state

        runway_inputs_usable = bool(
            getattr(
                pfd,
                "position_valid",
                False,
            )
            and watchdog.position_valid
            and watchdog.position_fresh
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        )

        if not runway_inputs_usable:
            return

        airport_id = (
            self.config.navigation
            .selected_waypoint_id
        )

        runway = self.database.best_runway(
            airport_id
        )

        if runway is None:
            return

        geometry = (
            self.runway_geometry_computer.compute(
                runway=runway,
                aircraft_lat_deg=pfd.latitude_deg,
                aircraft_lon_deg=pfd.longitude_deg,
                aircraft_alt_ft=pfd.indicated_alt_ft,
            )
        )

        if geometry is None:
            return

        projected = (
            self.runway_projection_computer.project(
                geometry=geometry,
                heading_deg=pfd.heading_deg,
                pitch_deg=pfd.pitch_deg,
                roll_deg=pfd.roll_deg,
                width_px=width,
                height_px=height,
            )
        )

        if (
            projected is None
            or not projected.visible
        ):
            return

        points = (
            projected.polygon_points
        )

        polygon = QPolygonF(
            [
                QPointF(
                    point.x_px,
                    point.y_px,
                )
                for point in points
            ]
        )

        painter.setPen(
            QPen(
                QColor(255, 255, 255),
                3,
            )
        )

        painter.setBrush(
            QBrush(
                QColor(45, 45, 45)
            )
        )

        painter.drawPolygon(polygon)

        low_center_x = (
            projected.low_left.x_px
            + projected.low_right.x_px
        ) / 2.0

        low_center_y = (
            projected.low_left.y_px
            + projected.low_right.y_px
        ) / 2.0

        high_center_x = (
            projected.high_left.x_px
            + projected.high_right.x_px
        ) / 2.0

        high_center_y = (
            projected.high_left.y_px
            + projected.high_right.y_px
        ) / 2.0

        painter.setPen(
            QPen(
                QColor(255, 255, 0),
                2,
            )
        )

        painter.drawLine(
            QPointF(
                low_center_x,
                low_center_y,
            ),
            QPointF(
                high_center_x,
                high_center_y,
            ),
        )

        painter.setPen(
            QColor(255, 255, 255)
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Weight.Bold,
            )
        )

        painter.drawText(
            QPointF(
                low_center_x + 8.0,
                low_center_y - 8.0,
            ),
            geometry.low_end.ident,
        )

        painter.drawText(
            QPointF(
                high_center_x + 8.0,
                high_center_y - 8.0,
            ),
            geometry.high_end.ident,
        )

    # BLAKE_SCENIC_TOPO_CONTOURS_V4
    @staticmethod
    def _v4_visuals_enabled() -> bool:
        # Explicitly opt in; the hardware and standard PFD paths are unchanged.
        return os.environ.get("BLAKE_PFD_V4_SCENIC_VISUALS") == "1"

    @staticmethod
    def _v4_contour_segments(a, b, c, *, interval_ft=100.0):
        """Interpolated contour segments from TRUE triangulated ground elevations.

        Returns (level_ft, point_a, point_b), with each point expressed
        as (north_ft, east_ft, up_ft) in existing aircraft-relative space.
        No terrain height, classification, or warning input is modified.
        """
        vertices = (a, b, c)
        if not all(isfinite(v.elevation_ft) for v in vertices):
            return ()
        low = min(v.elevation_ft for v in vertices)
        high = max(v.elevation_ft for v in vertices)
        if high - low < 1.0 or not isfinite(interval_ft) or interval_ft <= 0.0:
            return ()
        first = int(low // interval_ft) + 1
        last = int(high // interval_ft)
        # An upper limit prevents unusually steep tiles from overloading
        # the 20-Hz renderer; visual-only missing contours are acceptable.
        if last - first > 6:
            step = max(1, (last - first) // 6 + 1)
        else:
            step = 1
        segments = []
        for band in range(first, last + 1, step):
            level = band * interval_ft
            endpoints = []
            for left, right in ((a, b), (b, c), (c, a)):
                e0, e1 = left.elevation_ft, right.elevation_ft
                if not (min(e0, e1) < level <= max(e0, e1)):
                    continue
                t = (level - e0) / (e1 - e0)
                endpoints.append((
                    left.north_ft + t * (right.north_ft - left.north_ft),
                    left.east_ft + t * (right.east_ft - left.east_ft),
                    left.up_ft + t * (right.up_ft - left.up_ft),
                ))
            if len(endpoints) == 2:
                delta = sum((x - y) ** 2 for x, y in zip(*endpoints))
                if delta > 0.01:
                    segments.append((level, endpoints[0], endpoints[1]))
        return tuple(segments)

    @staticmethod
    def _v4_non_threat_inside_scenic_view(x, y, width, height):
        """Keep non-critical symbols off the left/right avionics panels."""
        return (
            width * 0.23 <= x <= width * 0.77
            and height * 0.14 <= y <= height * 0.93
        )

    # BLAKE_V5_REAL_RELIEF_COMPARISON
    @staticmethod
    def _v5_visuals_enabled() -> bool:
        return os.environ.get("BLAKE_PFD_V5_REAL_RELIEF") == "1"

    # BLAKE_V6_SRTM_STATUS_AND_MOUNTAIN_PRESENTATION
    @staticmethod
    def _v6_visuals_enabled() -> bool:
        return os.environ.get("BLAKE_PFD_V6_VISUALS") == "1"

    def _v6_mountain_scene(self) -> bool:
        return (
            self._v6_visuals_enabled()
            and not getattr(self, "use_hardware", False)
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
        )

    def _v6_demo_scene(self) -> bool:
        return (
            self._v6_visuals_enabled()
            and not getattr(self, "use_hardware", False)
            and (
                os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
                or os.environ.get("BLAKE_PFD_SCENIC_DEMO") == "1"
            )
        )

    @staticmethod
    def _v6_srtm_ground_sample(sampler, lat, lon, altitude_ft):
        """Display-only GND/AGL from the same SRTM sampler as the 3D mesh.

        Return None for invalid coordinates, absent/void data or broken sampler;
        never synthesize a ground elevation or substitute fallback terrain.
        """
        try:
            lat, lon, altitude_ft = float(lat), float(lon), float(altitude_ft)
            if (
                not all(isfinite(n) for n in (lat, lon, altitude_ft))
                or not -90.0 <= lat <= 90.0
                or not -180.0 <= lon <= 180.0
            ):
                return None
            ground_ft = sampler(lat, lon)
            if ground_ft is None or isinstance(ground_ft, bool):
                return None
            ground_ft = float(ground_ft)
            # Reject SRTM void sentinel (-32768) and impossible samples.
            if not isfinite(ground_ft) or not -1500.0 <= ground_ft <= 30000.0:
                return None
            return (ground_ft, altitude_ft - ground_ft)
        except (ValueError, TypeError, OSError, RuntimeError, IndexError):
            return None

    def _v6_current_srtm_status(self):
        pfd = getattr(self, "pfd", None)
        if pfd is None or not getattr(self, "real_terrain_enabled", False):
            return None
        return self._v6_srtm_ground_sample(
            self.terrain_sampler,
            pfd.latitude_deg,
            pfd.longitude_deg,
            pfd.indicated_alt_ft,
        )

    # BLAKE_V8_RIDGE_GEOMETRY: diagnostic; no modification to elevations,
    # terrain warning thresholds, world-to-camera transform, or clipping.
    def _v8_ridge_scene(self) -> bool:
        return (
            self._v6_mountain_scene()
            and os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
            and os.environ.get("BLAKE_PFD_V8_RIDGE_DEMO") == "1"
        )

    def _v9_high_ridge_scene(self) -> bool:
        """Optional 15,000-ft comparator, same location/heading as low ridge."""
        return (
            self._v8_ridge_scene()
            and os.environ.get("BLAKE_PFD_V9_HIGH_RIDGE") == "1"
        )

    # BLAKE_V10_RIDGE_MATERIALS -- strictly optional TEST SCENE visuals.
    def _v10_ridge_visuals(self) -> bool:
        return (
            not getattr(self, "use_hardware", True)
            and self._v8_ridge_scene()
            and os.environ.get("BLAKE_PFD_V10_RIDGE_VISUALS") == "1"
        )

    @staticmethod
    def _v10_ridge_ground_brush(horizon_height: int) -> QBrush:
        """Muted earth background behind TRUE SRTM mesh; never a height."""
        gradient = QLinearGradient(0, 0, 0, max(1, horizon_height * 2))
        gradient.setColorAt(0.0, QColor(80, 112, 104))
        gradient.setColorAt(1.0, QColor(43, 74, 67))
        return QBrush(gradient)

    @staticmethod
    def _v10_ridge_diagnostic_rects(width: int, height: int):
        """Keep diagnostic lines strictly left of the altitude tape."""
        x = width * 0.295
        w = width * 0.355
        return (
            QRectF(x, height * 0.155, w, 16),
            QRectF(x, height * 0.185, w, 16),
        )

    @staticmethod
    def _v10_safe_triangle_brush(points, average_color, vertex_light):
        """Shade NONHAZARD faces continuously; never distort elevations.

        A linear interpolation is a display-only approximation of blended
        per-vertex normals. Warning/critical faces never use this brush.
        """
        if len(points) != 3 or len(vertex_light) != 3:
            return QBrush(average_color)
        low = min(range(3), key=lambda i: vertex_light[i])
        high = max(range(3), key=lambda i: vertex_light[i])
        if vertex_light[high] - vertex_light[low] < 0.045:
            return QBrush(average_color)
        p0, p1 = points[low], points[high]
        if (p1.x_px - p0.x_px) ** 2 + (p1.y_px - p0.y_px) ** 2 < 16:
            return QBrush(average_color)
        mean_light = max(0.01, sum(vertex_light) / 3.0)
        gradient = QLinearGradient(
            QPointF(p0.x_px, p0.y_px), QPointF(p1.x_px, p1.y_px),
        )
        for location, index in ((0.0, low), (1.0, high)):
            scale = min(1.14, max(0.86, vertex_light[index] / mean_light))
            gradient.setColorAt(location, QColor(
                min(255, round(average_color.red() * scale)),
                min(255, round(average_color.green() * scale)),
                min(255, round(average_color.blue() * scale)),
            ))
        return QBrush(gradient)

    # BLAKE_V11_RIDGE_GOURAUD -- display-only smooth shading (ridge demo).
    def _v11_ridge_visuals(self) -> bool:
        """Additional opt-in; never active in hardware or normal flight PFD."""
        return (
            self._v10_ridge_visuals()
            and os.environ.get("BLAKE_PFD_V11_RIDGE_SHADING") == "1"
        )

    # BLAKE_V12_DEPTH_CAMERA -- opt-in stationary ridge visualization ONLY.
    def _v12_ridge_visuals(self) -> bool:
        return (
            self._v11_ridge_visuals()
            and os.environ.get("BLAKE_PFD_V12_RIDGE_DEPTH") == "1"
        )

    # BLAKE_V13_CINCINNATI_MOVING: opt-in, non-hardware renderer trial.
    def _v13_cincinnati_depth_enabled(self) -> bool:
        return (
            not getattr(self, "use_hardware", True)
            and os.environ.get("BLAKE_PFD_SCENIC_DEMO") == "1"
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") != "1"
            and os.environ.get("BLAKE_PFD_V13_CINCINNATI_DEPTH") == "1"
            and getattr(self, "real_terrain_enabled", False)
        )

    def _v13_cincinnati_diagnostics_enabled(self) -> bool:
        return (
            not getattr(self, "use_hardware", True)
            and os.environ.get("BLAKE_PFD_SCENIC_DEMO") == "1"
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") != "1"
            and os.environ.get("BLAKE_PFD_V13_CINCINNATI_DIAGNOSTICS") == "1"
        )

    # BLAKE_V14_CINCINNATI_PERFORMANCE: optional development experiment only.
    def _v14_cincinnati_optimize_enabled(self) -> bool:
        return (
            self._v13_cincinnati_depth_enabled()
            and os.environ.get("BLAKE_PFD_V14_OPTIMIZE") == "1"
        )

    def _v14_cincinnati_profile_enabled(self) -> bool:
        return (
            self._v13_cincinnati_diagnostics_enabled()
            and os.environ.get("BLAKE_PFD_V14_PROFILE") == "1"
        )

    @staticmethod
    def _v14_vertex_lights(surface, normals, min_elevation, span):
        """One lighting calculation per true SRTM vertex, NOT per face.

        Frame-local display colors only; never changes elevation, terrain
        hazard class, threshold, or projected polygon coordinates.
        """
        if normals is None or len(normals) != len(surface.vertices):
            return ()
        return tuple(
            BlakePfdDemo._v7_mountain_light(
                normals, (i, i, i),
                (vertex.elevation_ft - min_elevation) / span,
            )
            for i, vertex in enumerate(surface.vertices)
        )

    @staticmethod
    def _v14_gradient_worth_drawing(points, vertex_lights):
        """Avoid costly software gradients on tiny/near-uniform safe faces."""
        if len(points) != 3 or len(vertex_lights) != 3:
            return False
        try:
            if not all(isfinite(float(light)) for light in vertex_lights):
                return False
        except (TypeError, ValueError, OverflowError):
            return False
        if max(vertex_lights) - min(vertex_lights) < 0.07:
            return False
        try:
            x0, y0 = float(points[0].x_px), float(points[0].y_px)
            x1, y1 = float(points[1].x_px), float(points[1].y_px)
            x2, y2 = float(points[2].x_px), float(points[2].y_px)
        except (AttributeError, ValueError, TypeError):
            return False
        if not all(isfinite(n) for n in (x0, y0, x1, y1, x2, y2)):
            return False
        twice_area = abs((x1-x0)*(y2-y0)-(x2-x0)*(y1-y0))
        return twice_area >= 2100.0  # 1050 px²; bounded work on ARM64 emulation

    def _v14_record_paint(self, start_s, end_s):
        """Report UI paint-event cadence, not fabricated screen-refresh FPS."""
        if start_s is None:
            return
        elapsed = end_s - start_s
        if not (isfinite(elapsed) and 0.0 <= elapsed <= 10.0):
            self._v14_paint_ms = None
            self._v14_paint_hz = None
            self._v14_last_paint_start = None
            return
        self._v14_paint_ms = elapsed * 1000.0
        BlakePfdDemo._v15_record_metric(self, "paint", self._v14_paint_ms)
        BlakePfdDemo._v15_print_periodic_metrics(self)
        last_start = getattr(self, "_v14_last_paint_start", None)
        self._v14_last_paint_start = start_s
        if last_start is None:
            self._v14_paint_hz = None
            return
        frame_interval = start_s - last_start
        if not (isfinite(frame_interval) and 0.015 <= frame_interval <= 5.0):
            self._v14_paint_hz = None
            return
        measured = 1.0 / frame_interval
        previous = getattr(self, "_v14_paint_hz", None)
        self._v14_paint_hz = (
            measured if previous is None or not isfinite(previous)
            else (0.7 * previous + 0.3 * measured)
        )

    @staticmethod
    def _v15_sample_percentile(samples, percentile=0.95):
        """Finite, bounded paint-time summary; development telemetry only."""
        cleaned = sorted(
            float(value) for value in samples
            if isinstance(value, (int, float))
            and isfinite(value) and 0.0 <= value <= 60_000.0
        )
        if not cleaned:
            return None
        index = min(len(cleaned) - 1, max(0, int((len(cleaned) - 1) * percentile + 0.999999)))
        return cleaned[index]

    @staticmethod
    def _v15_fast_normal_skip(level, optimized, lights):
        """Only display calculations may be skipped; never hazard classification."""
        return level in ("WARNING", "CRITICAL") or (
            level == "NONE" and optimized and bool(lights)
        )

    def _v15_record_metric(self, name, sample):
        """In-memory bounded history for actual measured draw durations."""
        if not isinstance(sample, (int, float)) or not isfinite(sample):
            return
        if sample < 0.0 or sample > 60_000.0:
            return
        attribute = "_v15_metric_" + name
        history = getattr(self, attribute, ())
        setattr(self, attribute, (*history[-23:], float(sample)))

    def _v15_metric_p95(self, name):
        return self._v15_sample_percentile(
            getattr(self, "_v15_metric_" + name, ())
        )

    @staticmethod
    def _v15_terrain_diagnostic(last_ms, p95_ms):
        if last_ms is None or not isfinite(last_ms) or last_ms < 0:
            return "TERR DRAW N/A"
        if p95_ms is None or not isfinite(p95_ms) or p95_ms < 0:
            return f"TERR DRAW {last_ms:.0f} ms"
        return f"TERR {last_ms:.0f} ms | P95 {p95_ms:.0f} ms"

    def _v15_log_warning_transition(self, presentation):
        """Simulation-only event evidence; no alert timing/severity changes."""
        state = (
            (str(presentation.priority), str(presentation.message))
            if getattr(presentation, "visible", False) else None
        )
        previous = getattr(self, "_v15_previous_warning_state", "UNSET")
        self._v15_previous_warning_state = state
        if previous == state or (previous == "UNSET" and state is None):
            return
        print(
            "BLAKE_V15_WARN transition "
            + ("CLEARED" if state is None else f"{state[0]} {state[1]}")
            + " [presentation-only; thresholds unchanged]",
            flush=True,
        )

    def _v15_print_periodic_metrics(self):
        """Optional stdout breadcrumbs, never a flight-performance assertion."""
        if os.environ.get("BLAKE_PFD_V15_LOG_METRICS") != "1":
            return
        count = getattr(self, "_v15_metric_log_counter", 0) + 1
        self._v15_metric_log_counter = count
        if count % 24:
            return
        rate = getattr(self, "_v14_paint_hz", None)
        terrain = self._v15_metric_p95("terrain")
        total = self._v15_metric_p95("paint")
        print(
            "BLAKE_V15_PERF simulated PFD paint Hz="
            + (f"{rate:.2f}" if rate is not None else "N/A")
            + " paint_p95_ms="
            + (f"{total:.1f}" if total is not None else "N/A")
            + " terrain_p95_ms="
            + (f"{terrain:.1f}" if terrain is not None else "N/A"),
            flush=True,
        )

    @staticmethod
    def _v14_paint_diagnostic_line(paint_hz, paint_ms):
        if (
            paint_hz is None or paint_ms is None
            or not isfinite(paint_hz) or not isfinite(paint_ms)
            or paint_hz < 0 or paint_ms < 0
        ):
            return "PFD PAINT RATE N/A"
        return f"PFD PAINT {paint_hz:.1f} Hz | {paint_ms:.0f} ms"

    @staticmethod
    def _v13_cincinnati_warning_rects(width: int):
        """Only the center viewport is used; side engine/route panels stay clear."""
        # PFD artwork is designed for 1024x600, but bounds scale with width.
        central_left = width * 0.19
        central_right = width * 0.80
        span = max(0.0, central_right - central_left)
        return (
            QRectF(central_left, 1.0, span * 0.52, 30.0),
            QRectF(central_left, 32.0, span * 0.52, 35.0),
            QRectF(central_left + span * 0.54, 34.0,
                   span * 0.46, 31.0),
        )

    @staticmethod
    def _v13_diagnostic_text(pfd, watchdog, render_ms):
        """Display-only diagnostics. Never substitutes stale/fabricated GPS."""
        if not (
            pfd is not None and watchdog is not None
            and getattr(pfd, "position_valid", False)
            and getattr(watchdog, "position_valid", False)
            and getattr(watchdog, "position_fresh", False)
        ):
            gps = "GPS UNAVAILABLE"
        else:
            try:
                lat = float(pfd.latitude_deg)
                lon = float(pfd.longitude_deg)
                if not (isfinite(lat) and isfinite(lon)
                        and -90.0 <= lat <= 90.0
                        and -180.0 <= lon <= 180.0):
                    raise ValueError("invalid geographic coordinates")
                gps = f"GPS {lat:+.4f}, {lon:+.4f}"
            except (TypeError, ValueError, AttributeError):
                gps = "GPS UNAVAILABLE"
        if render_ms is None or not isfinite(render_ms) or render_ms < 0:
            duration = "TERR DRAW N/A"
        else:
            duration = f"TERR DRAW {render_ms:.1f} ms"
        return gps, duration

    def draw_v13_cincinnati_diagnostics(self, painter, width: int) -> None:
        if not self._v13_cincinnati_diagnostics_enabled():
            return
        gps, timing = self._v13_diagnostic_text(
            self.pfd,
            self.sensor_watchdog_state,
            getattr(self, "_v13_terrain_draw_ms", None),
        )
        profile = self._v14_cincinnati_profile_enabled()
        painter.save()
        # Debug overlay stays beneath red obstacles and safety banners.
        x = width * 0.29
        box_width = width * 0.36
        panel_height = 48 if profile else 34
        painter.fillRect(QRectF(x, 78, box_width, panel_height),
                         QColor(7, 19, 32, 170))
        painter.setPen(QPen(QColor(215, 241, 245), 1.0))
        painter.setFont(QFont("DejaVu Sans", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(x + 7, 78, box_width - 14, 17),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         gps)
        if not profile:
            painter.drawText(QRectF(x + 7, 95, box_width - 14, 17),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             timing)
        if profile:
            # V15: bounded rolling P95; no FPS guessed from terrain timing.
            terrain_p95 = self._v15_metric_p95("terrain")
            timing = self._v15_terrain_diagnostic(
                getattr(self, "_v13_terrain_draw_ms", None), terrain_p95
            )
            painter.drawText(
                QRectF(x + 7, 95, box_width - 14, 17),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                timing,
            )
            painter.drawText(
                QRectF(x + 7, 111, box_width - 14, 15),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self._v14_paint_diagnostic_line(
                    getattr(self, "_v14_paint_hz", None),
                    getattr(self, "_v14_paint_ms", None),
                ),
            )
        painter.restore()

    @staticmethod
    def _v12_depth_draw_order(surface, camera, heading_deg, pitch_deg, roll_deg):
        """Back-to-front painter order from true *camera-forward* depth.

        Strictly display-only; original terrain indices and hazard classes are
        never changed. Fall back to pre-V12 order if projection data are invalid.
        This is a painter's approximation, NOT a z-buffer or terrain safety tool.
        """
        triangles = surface.triangles
        fallback = tuple(range(len(triangles) - 1, -1, -1))
        try:
            orientation = camera.prepare_orientation(
                heading_deg=heading_deg, pitch_deg=pitch_deg,
                roll_deg=roll_deg,
            )
            if orientation is None:
                return fallback
            depths = []
            for vertex in surface.vertices:
                point = camera.world_to_camera_prepared(
                    north_ft=vertex.north_ft,
                    east_ft=vertex.east_ft,
                    up_ft=vertex.up_ft,
                    orientation=orientation,
                )
                if point is None or not isfinite(point.forward_ft):
                    return fallback
                depths.append(point.forward_ft)
            return tuple(sorted(
                range(len(triangles)),
                key=lambda index: (
                    -(
                        depths[triangles[index].first_index]
                        + depths[triangles[index].second_index]
                        + depths[triangles[index].third_index]
                    ) / 3.0,
                    index,
                ),
            ))
        except (AttributeError, IndexError, TypeError, ValueError):
            return fallback

    @staticmethod
    def _v12_depth_colors(surface, original_colors):
        """Extra subtle distance haze for SAFE SRTM vertices only.

        Uses actual world range; no displacement, no invented terrain elevations.
        The terrain classifier and alert colors are not inputs here.
        """
        if len(original_colors) != len(surface.vertices):
            return tuple(original_colors)
        colors = []
        for vertex, original in zip(surface.vertices, original_colors):
            distance_nm = (
                (vertex.north_ft ** 2 + vertex.east_ft ** 2) ** 0.5
                / 6076.12
            )
            haze = min(0.13, max(0.0, (distance_nm - 4.0) / 14.0 * 0.13))
            colors.append(QColor(*(
                max(0, min(255, round(channel * (1.0 - haze) + fog * haze)))
                for channel, fog in zip(original.getRgb()[:3], (145, 167, 179))
            )))
        return tuple(colors)

    @staticmethod
    def _v12_warning_text_rects(width: int):
        """Keep urgent banner text inside the central avionics viewport."""
        x = width * 0.184
        return (
            QRectF(x, 3.0, width * 0.52, 30.0),
            QRectF(x, 33.0, width * 0.255, 35.0),
            QRectF(width * 0.46, 37.0, width * 0.33, 29.0),
        )

    @staticmethod
    def _v11_ridge_subdivisions(points) -> int:
        """Bound work to at most 16 small polygons per large safe face."""
        if len(points) != 3:
            return 1
        maximum_squared = max(
            (points[i].x_px - points[(i + 1) % 3].x_px) ** 2
            + (points[i].y_px - points[(i + 1) % 3].y_px) ** 2
            for i in range(3)
        )
        if maximum_squared >= 160.0 ** 2:
            return 4
        if maximum_squared >= 88.0 ** 2:
            return 3
        if maximum_squared >= 42.0 ** 2:
            return 2
        return 1

    @classmethod
    def _v11_ridge_vertex_colors(cls, surface, vertex_normals):
        """Stable RGB at each shared TRUE SRTM vertex, lighting-only.

        Shared vertices have identical colors on adjacent safe triangles.
        No SRTM height, camera coordinate or hazard classification changes.
        """
        elevations = [v.elevation_ft for v in surface.vertices]
        if not elevations or len(elevations) != len(vertex_normals):
            return ()
        minimum = min(elevations)
        span = max(1.0, max(elevations) - minimum)
        colors = []
        for i, vertex in enumerate(surface.vertices):
            relative_height = (vertex.elevation_ft - minimum) / span
            alpine = max(0.0, min(1.0, (vertex.elevation_ft - 9700.0) / 3900.0))
            brightness = cls._v7_mountain_light(
                vertex_normals, (i, i, i), relative_height,
            )
            base = (
                76.0 + 73.0 * alpine,
                117.0 + 39.0 * alpine,
                72.0 + 73.0 * alpine,
            )
            distance_nm = (
                (vertex.north_ft ** 2 + vertex.east_ft ** 2) ** 0.5
                / 6076.12
            )
            atmosphere = min(0.43, max(0.0, (distance_nm - 1.5) / 11.0))
            rgb = tuple(
                max(0, min(255, round(
                    component * brightness * (1.0 - atmosphere)
                    + mist * atmosphere
                )))
                for component, mist in zip(base, (126, 149, 151))
            )
            colors.append(QColor(*rgb))
        return tuple(colors)

    @staticmethod
    def _v11_draw_smooth_triangle(painter, points, vertex_colors) -> int:
        """Approximate Gouraud shading with bounded screen-space subdivision.

        This *only* renders 2D subpolygons inside a projected safe triangle.
        The actual triangle geometry, world coordinates and depth are unchanged.
        Returns number of subpolygons drawn, useful for regressions.
        """
        if len(points) != 3 or len(vertex_colors) != 3:
            return 0
        divisions = BlakePfdDemo._v11_ridge_subdivisions(points)
        channels = tuple(color.getRgb()[:3] for color in vertex_colors)
        nodes = {}
        for i in range(divisions + 1):
            for j in range(divisions + 1 - i):
                weights = (
                    (divisions - i - j) / divisions,
                    i / divisions,
                    j / divisions,
                )
                xy = QPointF(
                    sum(weight * pt.x_px for weight, pt in zip(weights, points)),
                    sum(weight * pt.y_px for weight, pt in zip(weights, points)),
                )
                rgb = tuple(
                    sum(weight * channels[k][ch] for k, weight in enumerate(weights))
                    for ch in range(3)
                )
                nodes[i, j] = (xy, rgb)

        count = 0

        def draw_cell(keys):
            nonlocal count
            p0, c0 = nodes[keys[0]]
            p1, c1 = nodes[keys[1]]
            p2, c2 = nodes[keys[2]]
            color = QColor(*(
                max(0, min(255, round((c0[ch] + c1[ch] + c2[ch]) / 3.0)))
                for ch in range(3)
            ))
            # Matching thin edge paint hides Qt antialiasing pinholes.
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 0.65))
            painter.drawConvexPolygon(QPolygonF((p0, p1, p2)))
            count += 1

        for i in range(divisions):
            for j in range(divisions - i):
                draw_cell(((i, j), (i + 1, j), (i, j + 1)))
                if i + j < divisions - 1:
                    draw_cell(((i + 1, j), (i + 1, j + 1), (i, j + 1)))
        return count

    @staticmethod
    def _v8_projected_relief_diagnostic(
        surface, camera, *, heading_deg, pitch_deg, roll_deg,
        width_px, height_px, near_plane_ft,
    ):
        """Report REAL SRTM relief projected by the existing 3-D camera.

        A visible mesh vertex ABOVE the screen's level horizon is evidence
        of elevation in view, NOT a computed unobstructed ridgeline.
        Missing/no-data meshes return None, never an invented peak.
        """
        if not surface.valid or not surface.vertices:
            return None
        orientation = camera.prepare_orientation(
            heading_deg=heading_deg, pitch_deg=pitch_deg, roll_deg=roll_deg,
        )
        projection = camera.prepare_projection(
            width_px=width_px, height_px=height_px,
            near_plane_ft=near_plane_ft,
        )
        if orientation is None or projection is None:
            return None
        highest_elevation = max(v.elevation_ft for v in surface.vertices)
        highest_visible_angle_px = 0.0
        visible_vertex_count = 0
        for vertex in surface.vertices:
            point = camera.world_to_camera_prepared(
                north_ft=vertex.north_ft,
                east_ft=vertex.east_ft,
                up_ft=vertex.up_ft,
                orientation=orientation,
            )
            if point is None:
                continue
            projected = camera.project_prepared(point, projection=projection)
            if projected is None or not projected.visible:
                continue
            visible_vertex_count += 1
            highest_visible_angle_px = max(
                highest_visible_angle_px,
                0.5 * height_px - projected.y_px,
            )
        return (
            int(round(highest_elevation)),
            int(visible_vertex_count),
            int(round(highest_visible_angle_px)),
        )

    # BLAKE_V7_MOUNTAIN_SMOOTH_LIGHTING -- display-only (no height changes).
    @staticmethod
    def _v7_vertex_normals(surface):
        """Average nearby true terrain-face normals at shared mesh vertices.

        Only the shading receives these normals. The SRTM vertex positions,
        projection, mesh connectivity and terrain classification are unchanged.
        """
        vertices = surface.vertices
        totals = [[0.0, 0.0, 0.0] for _ in vertices]
        for triangle in surface.triangles:
            ia, ib, ic = (
                triangle.first_index,
                triangle.second_index,
                triangle.third_index,
            )
            a, b, c = vertices[ia], vertices[ib], vertices[ic]
            ab_e, ab_n, ab_u = (
                b.east_ft - a.east_ft,
                b.north_ft - a.north_ft,
                b.up_ft - a.up_ft,
            )
            ac_e, ac_n, ac_u = (
                c.east_ft - a.east_ft,
                c.north_ft - a.north_ft,
                c.up_ft - a.up_ft,
            )
            ne = ab_n * ac_u - ab_u * ac_n
            nn = ab_u * ac_e - ab_e * ac_u
            nu = ab_e * ac_n - ab_n * ac_e
            if nu < 0.0:
                ne, nn, nu = -ne, -nn, -nu
            magnitude = (ne * ne + nn * nn + nu * nu) ** 0.5
            if magnitude <= 1e-8:
                continue
            ne, nn, nu = ne / magnitude, nn / magnitude, nu / magnitude
            for index in (ia, ib, ic):
                totals[index][0] += ne
                totals[index][1] += nn
                totals[index][2] += nu
        normals = []
        for ne, nn, nu in totals:
            magnitude = (ne * ne + nn * nn + nu * nu) ** 0.5
            if magnitude <= 1e-8:
                normals.append((0.0, 0.0, 1.0))
            else:
                normals.append((ne / magnitude, nn / magnitude, nu / magnitude))
        return tuple(normals)

    @staticmethod
    def _v7_mountain_light(vertex_normals, indices, relative_height):
        """Soft terrain luminance from blended real slopes (not elevation)."""
        ne = sum(vertex_normals[i][0] for i in indices) / 3.0
        nn = sum(vertex_normals[i][1] for i in indices) / 3.0
        nu = sum(vertex_normals[i][2] for i in indices) / 3.0
        # Boost slope sensitivity in lighting ONLY; geometry remains exact.
        east, north, up = 2.4 * ne, 2.4 * nn, nu
        magnitude = (east * east + north * north + up * up) ** 0.5
        response = (
            (0.66 * east + 0.43 * north + 0.68 * up) / magnitude
            if magnitude > 1e-8 else 0.68
        )
        return max(0.72, min(1.20,
            0.80 + 0.35 * response + 0.08 * (relative_height - 0.5)
        ))

    def draw_synthetic_terrain(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        if self._v13_cincinnati_diagnostics_enabled():
            self._v13_terrain_draw_ms = None
        if not self.real_terrain_enabled:
            return

        surface = (
            self.synthetic_terrain_surface
        )

        if not surface.valid:
            return

        watchdog = (
            self.sensor_watchdog_state
        )

        if not (
            watchdog.position_valid
            and watchdog.position_fresh
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            return

        rebased_surface = (
            self.synthetic_terrain_rebaser.rebase(
                surface=surface,
                aircraft_lat_deg=(
                    pfd.latitude_deg
                ),
                aircraft_lon_deg=(
                    pfd.longitude_deg
                ),
                aircraft_alt_ft=(
                    pfd.indicated_alt_ft
                ),
            )
        )

        if not rebased_surface.valid:
            return

        projected = (
            self.synthetic_terrain_projection.project(
                surface=rebased_surface,
                heading_deg=pfd.heading_deg,
                pitch_deg=pfd.pitch_deg,
                roll_deg=pfd.roll_deg,
                width_px=width,
                height_px=height,
            )
        )

        if not projected.valid:
            return

        classified = (
            self.synthetic_terrain_classifier.classify(
                surface=rebased_surface,
                aircraft_altitude_ft=(
                    pfd.indicated_alt_ft
                ),
                vertical_speed_fpm=(
                    pfd.vsi_fpm
                ),
                ground_speed_kt=(
                    pfd.ground_speed_kt
                ),
            )
        )

        if not classified.valid:
            return

        # Measure the terrain paint path, excluding I/O, sensors and alerts.
        v13_draw_started = (
            monotonic() if self._v13_cincinnati_diagnostics_enabled()
            else None
        )

        if (
            len(projected.triangles)
            != len(classified.triangles)
        ):
            return

        terrain_brushes = {
            "NONE": QBrush(
                QColor(
                    75,
                    90,
                    45,
                )
            ),
            "CAUTION": QBrush(
                QColor(
                    190,
                    170,
                    0,
                )
            ),
            "WARNING": QBrush(
                QColor(
                    220,
                    110,
                    0,
                )
            ),
            "CRITICAL": QBrush(
                QColor(
                    200,
                    0,
                    0,
                )
            ),
        }

        # BLAKE_TERRAIN_VISUAL_SHADING_V1
        # Visual enhancement only: retain real SRTM geometry and
        # all terrain warning classifications without alteration.
        # Normalize elevation within the *currently displayed* mesh;
        # this changes color brightness, never terrain height.
        terrain_elevations = tuple(
            vertex.elevation_ft
            for vertex in rebased_surface.vertices
        )
        minimum_terrain_elevation = min(terrain_elevations)
        terrain_elevation_span = max(
            1.0,
            max(terrain_elevations) - minimum_terrain_elevation,
        )

        center_x = width // 2
        center_y = height // 2

        horizon_width = width
        horizon_height = height

        painter.save()

        painter.setClipRect(
            0,
            0,
            width,
            height,
        )

        # Do not draw a dark wireframe over the terrain. The pen is
        # instead set to each triangle's own shaded fill color below,
        # slightly covering anti-aliased gaps between mesh faces.

        # V5 adds stronger display-only hillshade from the actual 3D mesh.
        # Both the camera geometry and classifier still receive unmodified SRTM.
        v5_visuals = self._v5_visuals_enabled() and not getattr(
            self, "use_hardware", False
        )
        # V7: only the explicitly enabled stationary mountain demo. Cache
        # true mesh normals until the underlying SRTM terrain surface refreshes.
        v7_mountain = (
            os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
            and self._v6_mountain_scene()
        )
        v10_ridge = self._v10_ridge_visuals()
        v11_ridge = self._v11_ridge_visuals() if v10_ridge else False
        v12_ridge = self._v12_ridge_visuals() if v11_ridge else False
        v13_cincinnati = self._v13_cincinnati_depth_enabled()
        v14_optimize = self._v14_cincinnati_optimize_enabled()
        v7_vertex_normals = None
        if v7_mountain or v13_cincinnati:
            normals_cache = getattr(self, "_v7_normals_cache", None)
            if normals_cache is not None and normals_cache[0] is surface:
                v7_vertex_normals = normals_cache[1]
            else:
                v7_vertex_normals = self._v7_vertex_normals(rebased_surface)
                self._v7_normals_cache = (surface, v7_vertex_normals)

        # Scope this cache to the current paint. No stale SRTM or motion data.
        v14_vertex_light = (
            self._v14_vertex_lights(
                rebased_surface, v7_vertex_normals,
                minimum_terrain_elevation, terrain_elevation_span,
            ) if v14_optimize else ()
        )
        v11_colors = None
        if v11_ridge and v7_vertex_normals is not None:
            color_cache = getattr(self, "_v11_colors_cache", None)
            if color_cache is not None and color_cache[0] is surface:
                v11_colors = color_cache[1]
            else:
                v11_colors = self._v11_ridge_vertex_colors(
                    rebased_surface, v7_vertex_normals,
                )
                self._v11_colors_cache = (surface, v11_colors)
        if v12_ridge and v11_colors is not None:
            # One-time color adjustment per terrain refresh, not per frame.
            enhanced_cache = getattr(self, "_v12_colors_cache", None)
            if enhanced_cache is not None and enhanced_cache[0] is surface:
                v11_colors = enhanced_cache[1]
            else:
                v11_colors = self._v12_depth_colors(rebased_surface, v11_colors)
                self._v12_colors_cache = (surface, v11_colors)

        # Scenic-mode topographic contours use the SAME camera/real vertices.
        # Precompute its orientation only once per frame; standard/hardware
        # rendering never enters this optional branch.
        v4_visuals = self._v4_visuals_enabled() and not getattr(
            self, "use_hardware", False
        )
        if v5_visuals and os.environ.get("BLAKE_PFD_V5_CONTOURS") != "1":
            v4_visuals = False  # no unused camera/projection work
        topo_camera = self.synthetic_terrain_projection.camera
        if v4_visuals:
            topo_orientation = topo_camera.prepare_orientation(
                heading_deg=pfd.heading_deg,
                pitch_deg=pfd.pitch_deg,
                roll_deg=pfd.roll_deg,
            )
            topo_projection = topo_camera.prepare_projection(
                width_px=width, height_px=height,
                near_plane_ft=self.synthetic_terrain_projection.near_plane_ft,
            )
            v4_visuals = topo_orientation is not None and topo_projection is not None

        # V12 opt-in ridge test uses actual camera-forward depth to order
        # terrain faces. The normal application keeps its proven old order.
        # Classification lookup ALWAYS uses the original triangle index.
        if v12_ridge or v13_cincinnati:
            depth_key = (
                surface, pfd.indicated_alt_ft,
                pfd.heading_deg, pfd.pitch_deg, pfd.roll_deg,
            )
            depth_cache = getattr(self, "_v12_depth_cache", None)
            if (
                depth_cache is not None
                and depth_cache[0][0] is depth_key[0]
                and depth_cache[0][1:] == depth_key[1:]
            ):
                draw_indices = depth_cache[1]
            else:
                draw_indices = self._v12_depth_draw_order(
                    rebased_surface,
                    self.synthetic_terrain_projection.camera,
                    pfd.heading_deg, pfd.pitch_deg, pfd.roll_deg,
                )
                self._v12_depth_cache = (depth_key, draw_indices)
        else:
            # Previous projection surface ordering; no hardware-mode change.
            draw_indices = range(len(projected.triangles) - 1, -1, -1)

        for index in draw_indices:
            triangle = (
                projected.triangles[index]
            )

            if not triangle.visible:
                continue

            warning_level = (
                classified.triangles[index]
                .warning_level
            )

            brush = terrain_brushes.get(
                warning_level
            )

            if brush is None:
                continue

            polygon = QPolygonF(
                [
                    QPointF(
                        point.x_px,
                        point.y_px,
                    )
                    for point
                    in triangle.points
                ]
            )

            # Compute a light-facing normal from the true rebased
            # triangle geometry. Exaggeration is applied to *light*
            # contrast only; vertex heights remain unmodified.
            source_triangle = rebased_surface.triangles[index]
            a = rebased_surface.vertices[source_triangle.first_index]
            b = rebased_surface.vertices[source_triangle.second_index]
            c = rebased_surface.vertices[source_triangle.third_index]

            # V15: do not recompute a face normal when V14's already
            # calculated shared-vertex lighting will replace its result.
            # The RED/ORANGE hazard paths always use their exact base color.
            skip_face_normal = self._v15_fast_normal_skip(
                warning_level, v14_optimize, v14_vertex_light
            )
            mean_elevation = (
                a.elevation_ft + b.elevation_ft + c.elevation_ft
            ) / 3.0
            relative_height = (
                (mean_elevation - minimum_terrain_elevation)
                / terrain_elevation_span
            )
            if skip_face_normal:
                normal_east, normal_north, normal_up = 0.0, 0.0, 1.0
                brightness = 1.0
            else:
                ab_east = b.east_ft - a.east_ft
                ab_north = b.north_ft - a.north_ft
                ab_up = b.up_ft - a.up_ft
                ac_east = c.east_ft - a.east_ft
                ac_north = c.north_ft - a.north_ft
                ac_up = c.up_ft - a.up_ft

                normal_east = ab_north * ac_up - ab_up * ac_north
                normal_north = ab_up * ac_east - ab_east * ac_up
                normal_up = ab_east * ac_north - ab_north * ac_east
                if normal_up < 0.0:
                    normal_east = -normal_east
                    normal_north = -normal_north
                    normal_up = -normal_up

                # Amplifying lighting response slightly helps gentle
                # terrain read clearly without inventing elevations.
                light_east = 3.0 * normal_east
                light_north = 3.0 * normal_north
                light_up = normal_up
                normal_magnitude = (
                    light_east * light_east
                    + light_north * light_north
                    + light_up * light_up
                ) ** 0.5
                if normal_magnitude > 0.0:
                    illumination = (
                        light_east * 0.53
                        + light_north * 0.31
                        + light_up * 0.79
                    ) / normal_magnitude
                else:
                    illumination = 0.79

                # BLAKE_COMBINED_TERRAIN_TOWER_VISUAL_V2
                # More distinct light-facing slopes and actual elevation bands.
                # Visualization ONLY: no elevation, projection, or alert changes.
                # Strong WARNING/CRITICAL hazard colors remain exact below.
                brightness = (
                    0.84
                    + 0.49 * (illumination - 0.63)
                    + 0.27 * (relative_height - 0.5)
                )
                brightness = max(0.61, min(1.24, brightness))

            if v5_visuals and warning_level == "NONE" and not skip_face_normal:
                # Geometric sun angle with lighting-only slope sensitivity.
                # The underlying projection/elevations stay exactly as sampled.
                lit_east = 12.0 * normal_east
                lit_north = 12.0 * normal_north
                lit_up = normal_up
                lit_magnitude = (
                    lit_east * lit_east + lit_north * lit_north
                    + lit_up * lit_up
                ) ** 0.5
                if lit_magnitude > 0.0:
                    sun_response = (
                        0.62 * lit_east + 0.38 * lit_north
                        + 0.72 * lit_up
                    ) / lit_magnitude
                else:
                    sun_response = 0.72
                brightness = max(0.56, min(1.36, (
                    0.72 + 0.48 * sun_response
                    + 0.20 * (relative_height - 0.5)
                )))

            if v14_optimize and warning_level == "NONE" and v14_vertex_light:
                brightness = (
                    v14_vertex_light[source_triangle.first_index]
                    + v14_vertex_light[source_triangle.second_index]
                    + v14_vertex_light[source_triangle.third_index]
                ) / 3.0
            elif (v7_mountain or v13_cincinnati) and warning_level == "NONE":
                brightness = self._v7_mountain_light(
                    v7_vertex_normals,
                    (source_triangle.first_index, source_triangle.second_index,
                     source_triangle.third_index),
                    relative_height,
                )

            base_color = brush.color()
            if v5_visuals and warning_level == "NONE":
                # Natural earth/vegetation tones only for truly safe triangles.
                base_color = QColor(85, 119, 75)
                if self._v6_mountain_scene():
                    # Real elevation informs high-alpine rocky hue, never height.
                    alpine = max(0.0, min(1.0, (mean_elevation - 9700.0) / 3900.0))
                    base_color = QColor(
                        round(76.0 + 73.0 * alpine),
                        round(117.0 + 39.0 * alpine),
                        round(72.0 + 73.0 * alpine),
                    )
            shaded_color = QColor(
                min(255, max(0, round(base_color.red() * brightness))),
                min(255, max(0, round(base_color.green() * brightness))),
                min(255, max(0, round(base_color.blue() * brightness))),
            )
            # BLAKE_ROUTE_VISION_DISTANCE_ATMOSPHERE_V3
            # A faint atmospheric fade provides perspective depth using
            # TRUE triangle distance; no height/position is altered.
            # Never fade WARNING/CRITICAL hazard colors.
            if warning_level == "NONE":
                mean_north = (a.north_ft + b.north_ft + c.north_ft) / 3.0
                mean_east = (a.east_ft + b.east_ft + c.east_ft) / 3.0
                distance_nm = (
                    (mean_north ** 2 + mean_east ** 2) ** 0.5 / 6076.12
                )
                atmosphere = min(0.36, max(0.0, (distance_nm - 1.0) / 10.0))
                if v7_mountain:
                    # Mountain-only blue-gray depth cue using REAL range.
                    atmosphere = min(0.43, max(0.0, (distance_nm - 1.5) / 11.0))
                shaded_color = QColor(
                    round(shaded_color.red() * (1 - atmosphere) + 126 * atmosphere),
                    round(shaded_color.green() * (1 - atmosphere) + 149 * atmosphere),
                    round(shaded_color.blue() * (1 - atmosphere) + 151 * atmosphere),
                )
            # Preserve exact colors for immediate warnings, as validated
            # by existing pixel-level critical terrain tests.
            if warning_level in ("WARNING", "CRITICAL"):
                shaded_color = base_color
            painter.setPen(QPen(shaded_color, 0.8))
            # V11 uses smoothly varying shared-vertex colors on SAFE faces
            # in the opt-in ridge test ONLY. Exact hazard painting below is
            # intentionally unchanged and never has diminished opacity.
            if (
                v11_ridge
                and warning_level == "NONE"
                and v11_colors is not None
                and len(triangle.points) == 3
            ):
                vertex_indices = (
                    source_triangle.first_index,
                    source_triangle.second_index,
                    source_triangle.third_index,
                )
                self._v11_draw_smooth_triangle(
                    painter,
                    triangle.points,
                    tuple(v11_colors[vertex_index] for vertex_index in vertex_indices),
                )
            else:
                # V10 fallback for previous test modes / other scenes.
                if (
                    (v10_ridge or v13_cincinnati)
                    and warning_level == "NONE"
                    and v7_vertex_normals is not None
                    and len(triangle.points) == 3
                ):
                    vertex_indices = (
                        source_triangle.first_index,
                        source_triangle.second_index,
                        source_triangle.third_index,
                    )
                    vertex_light = (
                        tuple(v14_vertex_light[i] for i in vertex_indices)
                        if v14_optimize and v14_vertex_light else
                        tuple(
                            self._v7_mountain_light(
                                v7_vertex_normals,
                                (vertex_index, vertex_index, vertex_index),
                                (rebased_surface.vertices[vertex_index].elevation_ft
                                 - minimum_terrain_elevation) / terrain_elevation_span,
                            )
                            for vertex_index in vertex_indices
                        )
                    )
                    if (
                        v14_optimize
                        and not self._v14_gradient_worth_drawing(
                            triangle.points, vertex_light,
                        )
                    ):
                        painter.setBrush(QBrush(shaded_color))
                    else:
                        painter.setBrush(self._v10_safe_triangle_brush(
                            triangle.points, shaded_color, vertex_light,
                        ))
                else:
                    painter.setBrush(QBrush(shaded_color))

                painter.drawConvexPolygon(polygon)

            # BLAKE_SCENIC_TOPO_CONTOURS_V4
            # True topographic contours: intersections are computed in
            # three-dimensional world coordinates, then projected using
            # the SAME camera as the terrain. Nothing is exaggerated.
            # No contour is drawn over WARNING / CRITICAL hazard regions.
            if (
                v4_visuals
                and warning_level in ("NONE", "CAUTION")
                and (
                    not v5_visuals
                    or os.environ.get("BLAKE_PFD_V5_CONTOURS") == "1"
                )
            ):
                contour_color = (
                    QColor(180, 210, 156, 126)
                    if warning_level == "NONE"
                    else QColor(244, 234, 133, 92)
                )
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(contour_color, 1.0))
                for _level, start, end in self._v4_contour_segments(a, b, c):
                    points = []
                    for north_ft, east_ft, up_ft in (start, end):
                        camera_point = topo_camera.world_to_camera_prepared(
                            north_ft=north_ft, east_ft=east_ft, up_ft=up_ft,
                            orientation=topo_orientation,
                        )
                        if camera_point is None:
                            break
                        screen = topo_camera.project_prepared(
                            camera_point, projection=topo_projection,
                        )
                        if screen is None or not screen.visible:
                            break
                        points.append(QPointF(screen.x_px, screen.y_px))
                    if len(points) == 2:
                        painter.drawLine(points[0], points[1])

        # V8 ridge-only diagnostic. Uses exactly the same rebased SRTM
        # vertices and camera projection as the terrain polygons above.
        # This label does NOT claim a safe ridge clearance or visibility.
        if self._v8_ridge_scene():
            report = self._v8_projected_relief_diagnostic(
                rebased_surface,
                self.synthetic_terrain_projection.camera,
                heading_deg=pfd.heading_deg,
                pitch_deg=pfd.pitch_deg,
                roll_deg=pfd.roll_deg,
                width_px=width, height_px=height,
                near_plane_ft=self.synthetic_terrain_projection.near_plane_ft,
            )
            if report is not None:
                peak_ft, visible_vertices, above_horizon_px = report
                painter.setPen(QPen(QColor(230, 247, 251, 225), 1))
                if v10_ridge:
                    # Two short clipped lines in the unobstructed central
                    # sky; never underneath the altitude or engine tapes.
                    painter.setFont(QFont("DejaVu Sans", 7, QFont.Weight.Bold))
                    first, second = self._v10_ridge_diagnostic_rects(
                        width, height,
                    )
                    painter.drawText(
                        first,
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        f"SRTM PEAK {peak_ft:,} FT | {visible_vertices} VERT",
                    )
                    painter.drawText(
                        second,
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        f"MESH ABOVE HORIZON +{above_horizon_px} PX (NOT CLR)",
                    )
                else:
                    painter.setFont(QFont("DejaVu Sans", 8, QFont.Weight.Bold))
                    painter.drawText(
                        QPointF(width * 0.29, height * 0.21),
                        f"REAL SRTM MESH: MAX {peak_ft:,} FT | "
                        f"{visible_vertices} VISIBLE VERTICES | "
                        f"+{above_horizon_px} PX ABOVE HORIZON",
                    )

        # Clearly mark the stationary mountainous test to prevent its
        # unrelated flight plan readout being interpreted as true navigation.
        if (
            v5_visuals
            and os.environ.get("BLAKE_PFD_MOUNTAIN_DEMO") == "1"
        ):
            painter.setPen(QPen(QColor(255, 255, 255, 220), 1))
            painter.setFont(QFont("DejaVu Sans", 10, QFont.Weight.Bold))
            painter.drawText(
                QPointF(width * 0.38, height * 0.145),
                (
                    (
                        (
                            ("V12 HIGH RIDGE - STATIC / NOT FOR FLIGHT"
                             if self._v9_high_ridge_scene()
                             else "V12 LOW RIDGE - STATIC / NOT FOR FLIGHT")
                            if v12_ridge else
                            ("V11 HIGH RIDGE - STATIC / NOT FOR FLIGHT"
                             if self._v9_high_ridge_scene()
                             else "V11 LOW RIDGE - STATIC / NOT FOR FLIGHT")
                        )
                        if v11_ridge else
                        ("V9 HIGH RIDGE - STATIC / NOT FOR FLIGHT"
                         if self._v9_high_ridge_scene()
                         else "V8 RIDGE VIEW - STATIC / NOT FOR FLIGHT")
                    )
                    if self._v8_ridge_scene()
                    else "MOUNTAIN TEST - STATIC / NOT ROUTE"
                ),
            )

        painter.restore()
        if v13_draw_started is not None:
            self._v13_terrain_draw_ms = max(
                0.0, (monotonic() - v13_draw_started) * 1000.0
            )
            if self._v14_cincinnati_profile_enabled():
                self._v15_record_metric("terrain", self._v13_terrain_draw_ms)

    @staticmethod
    def _obstacle_mast_length_px(obstacle, symbol_radius: float) -> float:
        """Visual mast length; based on projected AGL, then capped for UI."""
        # BLAKE_V3_OBSTACLE_OPTIONAL_GEOMETRY_FIX_V1
        # Production projections carry numeric distance/AGL; small test
        # doubles may not. Missing *display-only* dimensions use the
        # previous schematic mast size, never inferred flight-safety data.
        base_y = getattr(obstacle, "base_y_px", None)
        if base_y is not None and isfinite(base_y):
            apparent_height = max(0.0, base_y - obstacle.y_px)
        else:
            distance_nm = getattr(obstacle, "distance_nm", None)
            height_agl_ft = getattr(obstacle, "height_agl_ft", None)
            if distance_nm is None or height_agl_ft is None:
                return 15.0
            if not (
                isfinite(distance_nm)
                and isfinite(height_agl_ft)
                and distance_nm >= 0.0
                and height_agl_ft >= 0.0
            ):
                return 15.0
            # Fallback if base projects outside the visible camera area.
            # Approximate angular height in screen pixels, not safety data.
            range_ft = max(0.1, distance_nm) * 6076.12
            apparent_height = 720.0 * height_agl_ft / range_ft
        return max(6.0, min(32.0, apparent_height - symbol_radius))

    def draw_synthetic_obstacles(
        self,
        painter: QPainter,
        pfd: FlightData,
        obstacle_state,
        width: int,
        height: int,
    ) -> None:
        if pfd is None:
            return

        if (
            obstacle_state is None
            or not obstacle_state.ok
            or not obstacle_state.nearby
        ):
            return

        watchdog = (
            self.sensor_watchdog_state
        )

        if not (
            watchdog.position_valid
            and watchdog.position_fresh
            and watchdog.attitude_valid
            and watchdog.attitude_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        ):
            return

        projected = (
            self.obstacle_projection_computer
            .project(
                obstacles=obstacle_state.nearby,
                aircraft_alt_ft=(
                    pfd.indicated_alt_ft
                ),
                heading_deg=pfd.heading_deg,
                pitch_deg=pfd.pitch_deg,
                roll_deg=pfd.roll_deg,
                width_px=width,
                height_px=height,
                warning_distance_nm=(
                    self.obstacles
                    .warning_distance_nm
                ),
                warning_clearance_ft=(
                    self.obstacles
                    .warning_clearance_ft
                ),
            )
        )

        # Tests may exercise projection without a
        # QPainter. Projection itself must still run.
        if painter is None:
            return

        if not projected:
            return

        # Projection was calculated exactly once with validated inputs.
        # Keep only RED threats for a safety-priority foreground pass.
        self._visible_obstacle_threats = [
            item for item in projected if item.threat
        ]

        painter.save()

        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        symbol_radius = 6.0

        # Declutter YELLOW obstacles in screen space.
        # Keep the nearest obstacle in each cluster.
        # RED threats are never removed and are always
        # drawn last so they remain visually dominant.
        non_threats = sorted(
            (
                obstacle
                for obstacle in projected
                if not obstacle.threat
            ),
            key=lambda obstacle: getattr(
                obstacle,
                "distance_nm",
                float("inf"),
            ),
        )

        # Increase spacing ONLY for non-threat yellow obstacle glyphs.
        # Every RED threat is kept, projected, and drawn without filtering.
        min_spacing_px = 43.0
        min_spacing_sq = (
            min_spacing_px
            * min_spacing_px
        )

        decluttered_non_threats = []

        for obstacle in non_threats:
            overlaps = any(
                (
                    (
                        obstacle.x_px
                        - kept.x_px
                    )
                    ** 2
                    + (
                        obstacle.y_px
                        - kept.y_px
                    )
                    ** 2
                )
                < min_spacing_sq
                for kept
                in decluttered_non_threats
            )

            if overlaps:
                continue

            decluttered_non_threats.append(
                obstacle
            )

        threats = [
            obstacle
            for obstacle in projected
            if obstacle.threat
        ]

        obstacles_to_draw = (
            decluttered_non_threats
            + threats
        )

        for obstacle in obstacles_to_draw:
            x = obstacle.x_px
            y = obstacle.y_px
            # BLAKE_SCENIC_TOPO_CONTOURS_V4
            # Non-threat symbols remain in the database and projection,
            # but the scenic view avoids painting them over avionics panels.
            # RED threats remain unfiltered in both drawing passes.
            if (
                self._v4_visuals_enabled()
                and not getattr(self, "use_hardware", False)
                and not obstacle.threat
                and not self._v4_non_threat_inside_scenic_view(
                    x, y, width, height
                )
            ):
                continue
            # Farther ordinary obstructions stay visible as smaller icons;
            # threats retain their full red diamonds at all distances.
            symbol_radius = (
                6.0 if obstacle.threat
                else max(3.5, 6.0 - 0.36 * getattr(obstacle, "distance_nm", 0.0))
            )

            color = (
                QColor(
                    255,
                    0,
                    0,
                )
                if obstacle.threat
                else QColor(
                    255,
                    220,
                    0,
                )
            )

            painter.setPen(
                QPen(
                    color,
                    2,
                )
            )

            diamond = QPolygonF(
                [
                    QPointF(
                        x,
                        y - symbol_radius,
                    ),
                    QPointF(
                        x + symbol_radius,
                        y,
                    ),
                    QPointF(
                        x,
                        y + symbol_radius,
                    ),
                    QPointF(
                        x - symbol_radius,
                        y,
                    ),
                ]
            )

            painter.drawPolygon(
                diamond
            )

            # Mast height reflects PROJECTED FAA height AGL when visible.
            # Min/max pixel bounds maintain legibility; NOT to scale.
            # Obstacle coordinates and threat flags remain unchanged.
            mast_top = y + symbol_radius
            mast_base = mast_top + self._obstacle_mast_length_px(
                obstacle, symbol_radius
            )
            painter.drawLine(QPointF(x, mast_top), QPointF(x - 5.0, mast_base))
            painter.drawLine(QPointF(x, mast_top), QPointF(x + 5.0, mast_base))
            mid_y = (mast_top + mast_base) / 2.0
            painter.drawLine(QPointF(x - 2.5, mid_y),
                             QPointF(x + 2.5, mid_y))
            painter.drawLine(QPointF(x - 5.0, mast_base),
                             QPointF(x + 5.0, mast_base))

        painter.restore()

    def draw_priority_obstacle_threats(
        self, painter: QPainter, width: int, height: int
    ) -> None:
        """Repaint validated red obstacle symbols above other PFD panels.

        Does NOT query the database, project another time, or change
        the safety/gating logic that decided whether threats are valid.
        """
        threats = getattr(self, "_visible_obstacle_threats", ())
        if not threats:
            return

        painter.save()
        try:
            painter.setClipRect(0, 0, width, height)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            for obstacle in threats:
                x = float(obstacle.x_px)
                y = float(obstacle.y_px)
                if not (isfinite(x) and isfinite(y)):
                    continue
                if not (0 <= x < width and 0 <= y < height):
                    continue

                r = 6.0
                painter.drawPolygon(
                    QPolygonF([
                        QPointF(x, y - r),
                        QPointF(x + r, y),
                        QPointF(x, y + r),
                        QPointF(x - r, y),
                    ])
                )
                # Repaint RED mast symbols above other display panels,
                # retaining the original high-priority red diamond.
                mast_top = y + r
                mast_base = mast_top + self._obstacle_mast_length_px(
                    obstacle, r
                )
                painter.drawLine(QPointF(x, mast_top),
                                 QPointF(x - 5.0, mast_base))
                painter.drawLine(QPointF(x, mast_top),
                                 QPointF(x + 5.0, mast_base))
                mid_y = (mast_top + mast_base) / 2.0
                painter.drawLine(QPointF(x - 2.5, mid_y),
                                 QPointF(x + 2.5, mid_y))
                painter.drawLine(QPointF(x - 5.0, mast_base),
                                 QPointF(x + 5.0, mast_base))
        finally:
            painter.restore()

    def draw_synthetic_vision(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
        obstacle_state=None,
    ) -> None:
        scene = self.synthetic_vision.update(pfd)

        self.draw_synthetic_terrain(
            painter,
            pfd,
            width,
            height,
        )

        self.draw_synthetic_runway(
            painter,
            pfd,
            width,
            height,
        )

        self.draw_synthetic_obstacles(
            painter,
            pfd,
            obstacle_state,
            width,
            height,
        )

        # BLAKE_SCENIC_TOPO_CONTOURS_V4: fewer, quieter DEMO-only gates.
        v4_visuals = self._v4_visuals_enabled() and not getattr(
            self, "use_hardware", False
        )
        visual_objects = scene.objects or []
        if self._v8_ridge_scene():
            # The stationary geometry test has no valid navigation route.
            visual_objects = []
        if v4_visuals:
            visual_objects = sorted(
                visual_objects,
                key=lambda candidate: getattr(
                    candidate, "distance_nm", float("inf")
                ),
            )[:2]
        for obj in visual_objects:
            x, y = project_object_to_screen(
                obj.rel_bearing_deg,
                obj.elevation_angle_deg,
                width,
                height,
                obj.distance_nm,
            )

            if not (0 <= x <= width and 0 <= y <= height):
                continue

            # BLAKE_ROUTE_VISION_GUIDANCE_STYLE_V3:
            # These are optional synthetic scene gates, NOT validated
            # navigation commands. Leave actual guidance state unchanged.
            box_w = int((36 if v4_visuals else 54) * obj.size)
            box_h = int((20 if v4_visuals else 29) * obj.size)

            painter.setPen(
                QPen(QColor(65, 225, 110, 80 if v4_visuals else 125), 1.5)
            )

            painter.setBrush(
                QBrush(
                    Qt.BrushStyle.NoBrush
                )
            )

            painter.drawRect(
                x - box_w // 2,
                y - box_h // 2,
                box_w,
                box_h,
            )

            painter.setPen(QPen(QColor(95, 230, 130, 105 if v4_visuals else 165), 1))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.drawText(
                x - 18,
                y - box_h // 2 - 5,
                obj.label,
            )

    def draw_attitude(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height // 2
        horizon_width = width
        horizon_height = height

        roll_deg = getattr(pfd, "roll_deg", 0.0)
        pitch_deg = getattr(pfd, "pitch_deg", 0.0)

        painter.save()
        painter.setClipRect(
            0,
            0,
            width,
            height,
        )

        painter.translate(center_x, center_y)
        painter.rotate(-roll_deg)
        # GARMIN REFERENCE: compact pitch presentation.
        painter.translate(0, pitch_deg * 5.2)

        painter.fillRect(-horizon_width, -horizon_height * 2, horizon_width * 2, horizon_height * 2, QColor(25, 95, 180))
        if self._v10_ridge_visuals():
            # V10: the old flat brown reference-ground plane was visible
            # wherever the TRUE SRTM mesh did not cover the attitude view.
            # Replace only its *background paint* in the test scene;
            # preserve the actual attitude horizon line and pitch ladder.
            painter.fillRect(
                -horizon_width, 0,
                horizon_width * 2, horizon_height * 2,
                self._v10_ridge_ground_brush(horizon_height),
            )
        else:
            painter.fillRect(-horizon_width, 0, horizon_width * 2, horizon_height * 2, QColor(125, 70, 25))

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(-horizon_width, 0, horizon_width, 0)

        self.draw_pitch_ladder(painter)
        painter.restore()

        painter.setPen(QPen(QColor(255, 220, 0), 4))
        painter.drawLine(center_x - 90, center_y, center_x - 25, center_y)
        painter.drawLine(center_x + 25, center_y, center_x + 90, center_y)
        painter.drawLine(center_x, center_y - 8, center_x, center_y + 8)

        self.draw_roll_scale(painter, center_x, center_y, horizon_height)

        # GARMIN REFERENCE:
        # Turn-rate cue belongs in the AHRS area, not below the HSI.
        self.draw_ahrs_turn_rate(
            painter,
            pfd,
            center_x,
            center_y,
            horizon_height,
        )

    def draw_ahrs_turn_rate(
        self,
        painter: QPainter,
        pfd: FlightData,
        center_x: int,
        center_y: int,
        horizon_height: int,
    ) -> None:
        """Draw Garmin-style white turn-rate cue in the AHRS field."""

        if not self.config.features.show_turn_rate:
            return

        # Position just below the roll arc and above the central AHRS symbol.
        y = center_y - int(horizon_height * 0.22)

        scale_half = 46

        painter.setPen(QPen(QColor(245, 245, 245), 2))

        # Compact turn-rate reference scale.
        painter.drawLine(
            center_x - scale_half,
            y,
            center_x + scale_half,
            y,
        )

        painter.drawLine(
            center_x - 30,
            y - 4,
            center_x - 30,
            y + 4,
        )

        painter.drawLine(
            center_x + 30,
            y - 4,
            center_x + 30,
            y + 4,
        )

        ratio = max(
            -1.5,
            min(
                1.5,
                pfd.turn_rate_deg_sec / 3.0,
            ),
        )

        pointer_x = center_x + int(ratio * 30)

        # White Garmin-style triangular pointer.
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 1))

        painter.drawPolygon(
            QPolygonF([
                QPointF(pointer_x, y + 2),
                QPointF(pointer_x - 6, y - 10),
                QPointF(pointer_x + 6, y - 10),
            ])
        )

    def draw_pitch_ladder(self, painter: QPainter) -> None:
        # GARMIN REFERENCE:
        # Smaller, tighter pitch ladder with unobtrusive labels.
        painter.setPen(QPen(QColor(245, 245, 245), 1.5))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        for pitch in range(-30, 35, 5):
            if pitch == 0:
                continue

            y = -pitch * 5.2

            if pitch % 10 == 0:
                line_half = 38
            else:
                line_half = 24

            painter.drawLine(
                int(-line_half),
                int(y),
                int(line_half),
                int(y),
            )

            if pitch % 10 == 0:
                label = str(abs(pitch))

                painter.drawText(
                    int(-line_half - 23),
                    int(y + 4),
                    label,
                )

                painter.drawText(
                    int(line_half + 7),
                    int(y + 4),
                    label,
                )

    def draw_roll_scale(self, painter: QPainter, center_x: int, center_y: int, horizon_height: int) -> None:
        # GARMIN REFERENCE: compact roll arc.
        radius = int(horizon_height * 0.32)
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
        # GARMIN REFERENCE: slim airspeed tape.
        tape_x, tape_y, tape_w = 22, 58, 86
        tape_h = height - 116
        center_y = tape_y + tape_h // 2
        ias = pfd.ias_kt

        # V9: do not inherit the previous glyph/attitude WHITE brush.
        # A bordered tape is an outline, never an opaque painted rectangle.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(15, 15, 20, 140))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        for speed in range(int(ias - 50), int(ias + 55), 10):
            # V7 static mountain camera: omit physically impossible
            # negative airspeed graduations around the zero-IAS marker.
            if (
                speed < 0
                and os.environ.get("BLAKE_PFD_V7_VISUALS") == "1"
                and self._v6_mountain_scene()
            ):
                continue
            y = center_y - int((speed - ias) * 4.0)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(
                    tape_x + tape_w - 25,
                    y,
                    tape_x + tape_w - 4,
                    y,
                )
                painter.drawText(
                    tape_x + 8,
                    y + 4,
                    str(speed),
                )

        painter.fillRect(
            tape_x + 4,
            center_y - 20,
            tape_w - 8,
            40,
            QColor(0, 0, 0, 220),
        )
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(
            tape_x + 4,
            center_y - 20,
            tape_w - 8,
            40,
        )
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(
            QRectF(
                tape_x + 4,
                center_y - 20,
                tape_w - 8,
                40,
            ),
            Qt.AlignmentFlag.AlignCenter,
            f"{ias:.0f}",
        )

    def draw_altitude_tape(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        # GARMIN REFERENCE: slim altitude tape.
        tape_w = 96
        tape_x = width - tape_w - 22
        tape_y = 58
        tape_h = height - 116
        center_y = tape_y + tape_h // 2
        alt = pfd.indicated_alt_ft

        # V9: do not inherit the previous glyph/attitude WHITE brush.
        # A bordered tape is an outline, never an opaque painted rectangle.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.fillRect(tape_x, tape_y, tape_w, tape_h, QColor(15, 15, 20, 140))
        painter.setPen(QPen(QColor(210, 210, 210), 2))
        painter.drawRect(tape_x, tape_y, tape_w, tape_h)

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        start_alt = int((alt - 1000) // 100) * 100
        end_alt = int((alt + 1100) // 100) * 100

        for altitude in range(start_alt, end_alt, 100):
            y = center_y - int(((altitude - alt) / 100.0) * 22.0)
            if tape_y < y < tape_y + tape_h:
                painter.drawLine(
                    tape_x + 4,
                    y,
                    tape_x + 26,
                    y,
                )
                painter.drawText(
                    tape_x + 31,
                    y + 4,
                    str(altitude),
                )

        painter.fillRect(
            tape_x + 4,
            center_y - 20,
            tape_w - 8,
            40,
            QColor(0, 0, 0, 220),
        )
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(
            tape_x + 4,
            center_y - 20,
            tape_w - 8,
            40,
        )
        painter.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        painter.drawText(
            QRectF(
                tape_x + 4,
                center_y - 20,
                tape_w - 8,
                40,
            ),
            Qt.AlignmentFlag.AlignCenter,
            f"{alt:.0f}",
        )

        # Keep the pilot-selected altimeter setting
        # continuously visible on the PFD.
        baro_setting_inhg = (
            self.flight_computer
            .baro_setting_controller
            .setting_inhg
        )

        baro_box_x = tape_x + 4
        baro_box_y = tape_y + tape_h - 27
        baro_box_w = tape_w - 8
        baro_box_h = 23

        painter.fillRect(
            baro_box_x,
            baro_box_y,
            baro_box_w,
            baro_box_h,
            QColor(
                0,
                0,
                0,
                190,
            ),
        )

        painter.setPen(
            QPen(
                QColor(
                    0,
                    220,
                    255,
                ),
                1,
            )
        )

        painter.drawRect(
            baro_box_x,
            baro_box_y,
            baro_box_w,
            baro_box_h,
        )

        painter.setFont(
            QFont(
                "Arial",
                10,
                QFont.Weight.Bold,
            )
        )

        painter.drawText(
            QRectF(
                baro_box_x,
                baro_box_y,
                baro_box_w,
                baro_box_h,
            ),
            Qt.AlignmentFlag.AlignCenter,
            f"BARO {baro_setting_inhg:.2f}",
        )

    def draw_vsi(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        # GARMIN REFERENCE: narrow VSI adjacent to altitude tape.
        x = width - 126
        y = 90
        h = height - 180
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
        """Draw a Garmin-inspired rotating HSI while preserving Blake PFD nav logic."""
        center_x = width // 2

        # GARMIN REFERENCE: larger HSI mounted lower in flight view.
        radius = min(108, max(88, int(width * 0.165)))
        center_y = height - radius - 28

        heading = pfd.heading_deg
        desired_track = pfd.desired_track_deg
        bearing = pfd.bearing_deg

        if self.direct_to_lateral_guidance_state.active:
            displayed_cdi = self.direct_to_lateral_guidance_state.lateral_error
        else:
            displayed_cdi = pfd.cdi

        displayed_cdi = max(-1.0, min(1.0, displayed_cdi))

        # GARMIN REFERENCE:
        # Dark glass HSI face while retaining synthetic-vision context.
        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 155)))

        painter.drawEllipse(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2,
        )

        # Outer compass ring.
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.setPen(QPen(QColor(235, 235, 235), 2))
        painter.drawEllipse(
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2,
        )

        # ------------------------------------------------------------------
        # Rotating compass card: minor marks every 10 degrees,
        # major marks and labels every 30 degrees.
        # ------------------------------------------------------------------
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        cardinal = {
            0: "N",
            90: "E",
            180: "S",
            270: "W",
        }

        for deg in range(0, 360, 10):
            relative = (deg - heading + 360.0) % 360.0
            angle = radians(relative - 90.0)

            major = deg % 30 == 0
            tick_len = 12 if major else 6

            outer_x = center_x + int(cos(angle) * radius)
            outer_y = center_y + int(sin(angle) * radius)
            inner_x = center_x + int(cos(angle) * (radius - tick_len))
            inner_y = center_y + int(sin(angle) * (radius - tick_len))

            painter.setPen(
                QPen(
                    QColor(245, 245, 245),
                    2 if major else 1,
                )
            )
            painter.drawLine(inner_x, inner_y, outer_x, outer_y)

            if major:
                label_radius = radius - 27
                label_x = center_x + int(cos(angle) * label_radius)
                label_y = center_y + int(sin(angle) * label_radius)

                label = cardinal.get(deg, f"{deg // 10:02d}")

                painter.drawText(
                    label_x - 12,
                    label_y + 5,
                    label,
                )

        # Fixed lubber line / current-heading pointer at twelve o'clock.
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawPolygon(
            QPolygonF([
                QPointF(center_x, center_y - radius + 3),
                QPointF(center_x - 7, center_y - radius + 15),
                QPointF(center_x + 7, center_y - radius + 15),
            ])
        )

        # Current heading value box.
        hdg_text = f"{heading % 360:03.0f}°"
        painter.setPen(QPen(QColor(210, 210, 210), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawRect(
            center_x - 30,
            center_y - radius - 1,
            60,
            24,
        )
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(
            center_x - 23,
            center_y - radius + 17,
            hdg_text,
        )

        # V9 RIDGE DEMO: There is no active route in this stationary camera.
        # Draw only the heading compass and a fixed aircraft marker; do not
        # render a magenta course needle/CDI or misleading NAV indications.
        # The real navigation code below remains unchanged in every other mode.
        if getattr(self, "_v8_ridge_scene", lambda: False)():
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(center_x, center_y - 13, center_x, center_y + 13)
            painter.drawLine(center_x - 15, center_y,
                             center_x + 15, center_y)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(210, 225, 235))
            painter.drawText(center_x - 31, center_y + radius - 14,
                             "NO ROUTE")
            return

        # ------------------------------------------------------------------
        # Desired-track/course needle.
        # Existing lateral guidance source is preserved.
        # ------------------------------------------------------------------
        course_relative = (desired_track - heading + 360.0) % 360.0
        course_angle = radians(course_relative - 90.0)
        cross_angle = course_angle + radians(90.0)

        course_r = radius - 31

        course_dx = cos(course_angle)
        course_dy = sin(course_angle)
        cross_dx = cos(cross_angle)
        cross_dy = sin(cross_angle)

        magenta = QColor(255, 0, 255)

        # Course shaft.
        painter.setPen(QPen(magenta, 4))
        painter.drawLine(
            center_x - int(course_dx * course_r),
            center_y - int(course_dy * course_r),
            center_x + int(course_dx * course_r),
            center_y + int(course_dy * course_r),
        )

        # Course arrow head.
        tip_x = center_x + int(course_dx * course_r)
        tip_y = center_y + int(course_dy * course_r)

        base_x = center_x + int(course_dx * (course_r - 22))
        base_y = center_y + int(course_dy * (course_r - 22))

        painter.setBrush(QBrush(magenta))
        painter.setPen(QPen(magenta, 2))
        painter.drawPolygon(
            QPolygonF([
                QPointF(tip_x, tip_y),
                QPointF(
                    base_x + int(cross_dx * 10),
                    base_y + int(cross_dy * 10),
                ),
                QPointF(
                    base_x - int(cross_dx * 10),
                    base_y - int(cross_dy * 10),
                ),
            ])
        )

        # CDI deviation reference dots.
        painter.setPen(QPen(QColor(235, 235, 235), 2))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        dot_spacing = 20

        for dot in (-2, -1, 1, 2):
            dot_x = center_x + int(cross_dx * dot * dot_spacing)
            dot_y = center_y + int(cross_dy * dot * dot_spacing)

            painter.drawEllipse(
                dot_x - 3,
                dot_y - 3,
                6,
                6,
            )

        # Moving CDI deviation bar. Full-scale deflection = 40 pixels.
        deviation = displayed_cdi * 40.0

        dev_center_x = center_x + int(cross_dx * deviation)
        dev_center_y = center_y + int(cross_dy * deviation)

        deviation_half_length = 28

        painter.setPen(QPen(magenta, 6))
        painter.drawLine(
            dev_center_x - int(course_dx * deviation_half_length),
            dev_center_y - int(course_dy * deviation_half_length),
            dev_center_x + int(course_dx * deviation_half_length),
            dev_center_y + int(course_dy * deviation_half_length),
        )

        # ------------------------------------------------------------------
        # Bearing pointer.
        # ------------------------------------------------------------------
        bearing_relative = (bearing - heading + 360.0) % 360.0
        bearing_angle = radians(bearing_relative - 90.0)

        bearing_r = radius - 42
        bearing_dx = cos(bearing_angle)
        bearing_dy = sin(bearing_angle)

        painter.setPen(QPen(QColor(0, 220, 255), 2))
        painter.drawLine(
            center_x,
            center_y,
            center_x + int(bearing_dx * bearing_r),
            center_y + int(bearing_dy * bearing_r),
        )

        bearing_tip_x = center_x + int(bearing_dx * bearing_r)
        bearing_tip_y = center_y + int(bearing_dy * bearing_r)

        painter.setBrush(QBrush(QColor(0, 220, 255)))
        painter.drawEllipse(
            bearing_tip_x - 4,
            bearing_tip_y - 4,
            8,
            8,
        )

        # Fixed Garmin-style aircraft symbol at HSI center.
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        painter.drawLine(
            center_x,
            center_y - 14,
            center_x,
            center_y + 15,
        )
        painter.drawLine(
            center_x - 17,
            center_y,
            center_x + 17,
            center_y,
        )
        painter.drawLine(
            center_x - 8,
            center_y + 11,
            center_x + 8,
            center_y + 11,
        )

        # Course / navigation information inside lower HSI.
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        painter.setPen(magenta)
        painter.drawText(
            center_x - radius + 14,
            center_y + radius - 14,
            f"CRS {desired_track % 360:03.0f}°",
        )

        source_label = (
            "DTO"
            if self.direct_to_lateral_guidance_state.active
            else "NAV"
        )

        painter.drawText(
            center_x + 35,
            center_y + radius - 14,
            source_label,
        )

        if self.config.obs.enabled:
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(
                center_x - 35,
                center_y + radius + 3,
                f"OBS {self.config.obs.selected_course_deg:.0f}°",
            )

    def draw_turn_and_slip(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        """Draw Garmin-style slip/skid beneath the HSI."""

        if not self.config.features.show_slip_skid:
            return

        center_x = width // 2

        radius = min(
            108,
            max(
                88,
                int(width * 0.165),
            ),
        )

        hsi_center_y = height - radius - 28

        # GARMIN REFERENCE:
        # Rounded black slip/skid enclosure immediately beneath HSI.
        panel_x = center_x - 145
        panel_y = hsi_center_y + radius - 1
        panel_w = 290
        panel_h = 52

        painter.setBrush(
            QBrush(
                QColor(
                    0,
                    0,
                    0,
                    220,
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    80,
                    80,
                    85,
                ),
                2,
            )
        )

        painter.drawRoundedRect(
            panel_x,
            panel_y,
            panel_w,
            panel_h,
            10,
            10,
        )

        ball_y = panel_y + 28

        max_offset = 66

        ball_x = center_x + int(
            max(
                -1.0,
                min(
                    1.0,
                    pfd.slip_skid,
                ),
            )
            * max_offset
        )

        # Dark recessed track.
        painter.setPen(
            QPen(
                QColor(
                    65,
                    65,
                    70,
                ),
                8,
            )
        )

        painter.drawLine(
            center_x - 96,
            ball_y,
            center_x + 96,
            ball_y,
        )

        # White reference marks.
        painter.setPen(
            QPen(
                QColor(
                    240,
                    240,
                    240,
                ),
                2,
            )
        )

        painter.drawLine(
            center_x - 42,
            ball_y - 8,
            center_x - 42,
            ball_y + 8,
        )

        painter.drawLine(
            center_x + 42,
            ball_y - 8,
            center_x + 42,
            ball_y + 8,
        )

        # L / R labels.
        painter.setFont(
            QFont(
                "Arial",
                9,
                QFont.Weight.Bold,
            )
        )

        painter.drawText(
            panel_x + 20,
            panel_y + 34,
            "L",
        )

        painter.drawText(
            panel_x + panel_w - 28,
            panel_y + 34,
            "R",
        )

        # Slip/skid ball.
        painter.setBrush(
            QBrush(
                QColor(
                    255,
                    255,
                    255,
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    220,
                    220,
                    220,
                ),
                1,
            )
        )

        painter.drawEllipse(
            ball_x - 8,
            ball_y - 8,
            16,
            16,
        )

    def draw_nav_cdi_vdi(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        features = self.config.features
        watchdog = self.sensor_watchdog_state
        position_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )
        air_data_usable = bool(
            watchdog.air_data_valid
            and watchdog.air_data_fresh
        )

        center_x = width // 2
        center_y = height // 2

        if features.show_cdi and not features.show_hsi and position_usable:
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

        if (
            features.show_vdi
            and self.config.vnav.enabled
            and position_usable
            and air_data_usable
        ):
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
        """Draw Garmin-style route/navigation status bar."""
        watchdog = self.sensor_watchdog_state

        position_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

        # Garmin-style dark header.
        bar_h = 36
        painter.save()
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setBrush(QBrush(QColor(8, 8, 10, 235)))
        painter.drawRect(0, 0, width, bar_h)

        active_leg = self.route_manager.get_active_leg()

        # ------------------------------------------------------------
        # Route / Direct-To source
        # ------------------------------------------------------------
        if self.direct_to_lateral_guidance_state.active:
            waypoint_id = getattr(
                self.config.navigation,
                "selected_waypoint_id",
                "---",
            )
            route_text = f"DTO → {waypoint_id}"

            dto_distance = getattr(
                self.direct_to_guidance_state,
                "distance_nm",
                None,
            )
            distance_nm = (
                dto_distance
                if dto_distance is not None
                else pfd.distance_to_waypoint_nm
            )
        else:
            distance_nm = pfd.distance_to_waypoint_nm

            if active_leg is not None:
                route_text = (
                    f"{active_leg.from_ident} → "
                    f"{active_leg.to_ident}"
                )
            else:
                waypoint_id = getattr(
                    self.config.navigation,
                    "selected_waypoint_id",
                    "---",
                )
                route_text = f"→ {waypoint_id}"

        desired_track = pfd.desired_track_deg

        ground_track = getattr(
            pfd,
            "ground_track_deg",
            getattr(
                pfd,
                "track_deg",
                pfd.heading_deg,
            ),
        )

        ground_speed = pfd.ground_speed_kt

        # ------------------------------------------------------------
        # ETE
        # ------------------------------------------------------------
        if (
            position_usable
            and ground_speed > 1.0
            and distance_nm is not None
        ):
            ete_minutes = max(
                0,
                int(round((distance_nm / ground_speed) * 60.0)),
            )
            ete_text = f"{ete_minutes // 60:d}:{ete_minutes % 60:02d}"
        else:
            ete_text = "--:--"

        if position_usable:
            dtk_text = f"{desired_track % 360:03.0f}°"
            dis_text = f"{distance_nm:.1f} NM"
            gs_text = f"{ground_speed:.0f} KT"
            trk_text = f"{ground_track % 360:03.0f}°"
        else:
            dtk_text = "---"
            dis_text = "--- NM"
            gs_text = "--- KT"
            trk_text = "---"

        # BLAKE_V6_NO_FALSE_ROUTE: the camera scene has no active test route.
        # Never show unrelated Cincinnati distance, DTK or ETE values.
        if self._v6_mountain_scene():
            route_text = "MOUNTAIN TEST"
            dtk_text = "---"
            dis_text = "--- NM"
            ete_text = "--:--"
            trk_text = "---"

        # ------------------------------------------------------------
        # Route section - left
        # ------------------------------------------------------------
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(255, 0, 255))
        painter.drawText(
            QRectF(10, 0, 185, bar_h),
            Qt.AlignmentFlag.AlignVCenter
            | Qt.AlignmentFlag.AlignLeft,
            route_text,
        )

        # ------------------------------------------------------------
        # Navigation data cells
        # ------------------------------------------------------------
        cells = [
            ("DTK", dtk_text),
            ("DIS", dis_text),
            ("ETE", ete_text),
            ("GS", gs_text),
            ("TRK", trk_text),
        ]

        x = 195
        cell_w = 88

        for label, value in cells:
            painter.setPen(QPen(QColor(65, 65, 70), 1))
            painter.drawLine(x, 2, x, bar_h - 2)

            painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
            painter.setPen(QColor(170, 170, 175))
            painter.drawText(
                QRectF(x + 5, 3, cell_w - 10, 11),
                Qt.AlignmentFlag.AlignLeft,
                label,
            )

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                QRectF(x + 5, 13, cell_w - 10, 19),
                Qt.AlignmentFlag.AlignLeft,
                value,
            )

            x += cell_w

        # ------------------------------------------------------------
        # Radio area - reserve Garmin-style right side now.
        # Actual COM/NAV radio values can be connected once we identify
        # the radio-data source in Blake PFD.
        # ------------------------------------------------------------
        radio_x = max(x, width - 175)

        painter.setPen(QPen(QColor(65, 65, 70), 1))
        painter.drawLine(radio_x, 2, radio_x, bar_h - 2)

        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        painter.setPen(QColor(170, 170, 175))
        painter.drawText(radio_x + 8, 12, "COM1")
        painter.drawText(radio_x + 88, 12, "NAV1")

        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(QColor(0, 220, 255))
        painter.drawText(radio_x + 8, 28, "---.---")
        painter.drawText(radio_x + 88, 28, "---.--")

        painter.restore()

    def draw_bottom_data_bar(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:

        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
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

        watchdog = self.sensor_watchdog_state

        position_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

        if not position_usable:
            parts = [
                "TRK ---",
                "BRG ---",
                "DTK ---",
            ]

            if self.config.obs.enabled:
                parts.append(
                    f"OBS {self.config.obs.selected_course_deg:.0f}°"
                )

            parts.append("CDI ---")

            if (
                self.config.features.show_vdi
                and self.config.vnav.enabled
            ):
                parts.append("VDI ---")

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
            return

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
            if (
                watchdog.air_data_valid
                and watchdog.air_data_fresh
            ):
                parts.append(
                    f"VDI {pfd.vdi:+.2f}°"
                )
            else:
                parts.append("VDI ---")

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
        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        box_x = 842
        box_y = 438
        box_w = 172
        box_h = 72

        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 16, "VNAV")
        watchdog = self.sensor_watchdog_state
        position_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )
        target_altitude_text = (
            f"TGT ALT {pfd.glidepath_target_alt_ft:.0f}"
            if position_usable
            else "TGT ALT ---"
        )
        painter.drawText(box_x + 10, box_y + 32, target_altitude_text)
        watchdog = self.sensor_watchdog_state
        vertical_guidance_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
            and watchdog.air_data_valid
            and watchdog.air_data_fresh
        )
        altitude_error_text = (
            f"ALT ERR {pfd.glidepath_alt_error_ft:+.0f}"
            if vertical_guidance_usable
            else "ALT ERR ---"
        )
        painter.drawText(box_x + 10, box_y + 48, altitude_error_text)
        painter.drawText(box_x + 10, box_y + 64, f"GP {self.config.vnav.glidepath_angle_deg:.1f}°")

    def draw_waypoint_info_box(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        watchdog = self.sensor_watchdog_state
        position_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

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
            f"BRG {bearing_deg:.0f}°" if position_usable else "BRG ---",
        )

        painter.drawText(
            box_x + 120,
            box_y + 52,
            f"DIS {distance_nm:.1f}NM" if position_usable else "DIS ---",
        )

        painter.drawText(
            box_x + 10,
            box_y + 75,
            f"CRS ERR {course_error_deg:+.0f}°"
            if position_usable else "CRS ERR ---",
        )

    def draw_navigation_status_box(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        watchdog = self.sensor_watchdog_state
        position_usable = bool(
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        )

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
            f"DTK {desired_track_deg:.0f}°" if position_usable else "DTK ---",
        )

        painter.drawText(
            box_x + 120,
            box_y + 52,
            f"BRG {bearing_deg:.0f}°" if position_usable else "BRG ---",
        )

        painter.drawText(
            box_x + 10,
            box_y + 76,
            f"DIS {distance_nm:.1f} NM" if position_usable else "DIS ---",
        )

    def draw_nearest_airports_overlay(self, painter: QPainter, pfd: FlightData, width: int, height: int) -> None:
        # PFD_HIDE_NEAREST_OVERLAY
        return

        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        watchdog = self.sensor_watchdog_state

        if not (
            pfd.position_valid
            and watchdog.position_valid
            and watchdog.position_fresh
        ):
            return

        nearest = self.database.nearest_airports(
            pfd.latitude_deg,
            pfd.longitude_deg,
            max_results=5,
        )

        box_x, box_y, box_w, box_h = 20, height - 210, 330, 165
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        y = box_y + 28
        painter.drawText(box_x + 10, y, "NEAREST AIRPORTS")
        y += 25

        for distance_nm, airport in nearest:
            painter.drawText(box_x + 10, y, f"{airport.ident:<5} {distance_nm:>4.1f}NM {airport.name[:24]}")
            y += 22

    def draw_moving_map(
        self,
        painter: QPainter,
        pfd: FlightData,
        width: int,
        height: int,
    ) -> None:
        """Full-screen MAP page using the existing moving-map computer.

        A stale/unavailable GPS position must not be used to fetch map airports.
        This display method does not alter navigation or warning state.
        """
        watchdog = getattr(self, "sensor_watchdog_state", None)
        position_usable = bool(
            pfd is not None
            and getattr(pfd, "position_valid", False)
            and watchdog is not None
            and getattr(watchdog, "position_valid", False)
            and getattr(watchdog, "position_fresh", False)
        )
        if not position_usable:
            self.map_airport_markers = []
            painter.save()
            painter.setPen(QPen(QColor(255, 180, 0), 2))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            painter.drawText(
                QRectF(40, 100, max(100, width - 160), 70),
                Qt.AlignmentFlag.AlignCenter,
                "MAP POSITION UNAVAILABLE",
            )
            painter.restore()
            return

        map_state = self.moving_map.update(
            database=self.database,
            aircraft_lat=pfd.latitude_deg,
            aircraft_lon=pfd.longitude_deg,
            range_nm=self.map_range_nm,
        )
        self.draw_moving_map_overlay(
            painter, map_state, width, height, full_page=True,
        )

    def draw_touch_map_controls(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        """Draw MAP controls from the same touch rectangles used for input."""
        self.touch_map_state = self.touch_map_controls.layout(
            screen_width=width,
            screen_height=height,
        )
        painter.save()
        painter.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        for button in self.touch_map_state.buttons:
            bounds = button.bounds
            rect = QRectF(bounds.x, bounds.y, bounds.width, bounds.height)
            painter.setBrush(QBrush(QColor(27, 47, 67, 238)))
            painter.setPen(QPen(QColor(0, 185, 245), 2))
            painter.drawRoundedRect(rect, 9.0, 9.0)
            painter.setPen(QPen(QColor(245, 245, 245), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, button.label)
        painter.restore()

    def draw_moving_map_overlay(
        self,
        painter: QPainter,
        map_state,
        width: int,
        height: int,
        full_page: bool = False,
    ) -> None:
        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        # GARMIN REDESIGN: shared lower-left tabbed pane.
        if full_page:
            # Leave the touch-control column and bottom navigation unobscured.
            box_x = 28
            box_y = 78
            box_w = max(170, width - 156)
            box_h = max(215, height - 166)
        else:
            box_x = 5
            box_y = 350
            box_w = 170
            box_h = 215

        # ----------------------------------------------------
        # Garmin-style pane frame and tabs.
        # WEATHER is visually selected to match master reference.
        # Underlying MAP / WEATHER / TRAFFIC drawing remains active.
        # ----------------------------------------------------
        painter.setBrush(
            QBrush(
                QColor(
                    0,
                    0,
                    0,
                    185,
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    105,
                    105,
                    110,
                ),
                1,
            )
        )

        painter.drawRect(
            box_x,
            box_y,
            box_w,
            box_h,
        )

        if full_page:
            # MAP mode has actual zoom/orientation buttons on the right.
            # Do not display the inset's decorative, noninteractive tabs.
            tab_h = 0
            content_top = box_y
        else:
            tab_h = 22
            tab_w = box_w / 3.0

            labels = ("TRAFFIC", "WEATHER", "MAP")

            painter.setFont(
                QFont(
                    "Arial",
                    8,
                    QFont.Weight.Bold,
                )
            )

            for index, label in enumerate(labels):
                tab_x = box_x + int(index * tab_w)

                selected = (label == "WEATHER")

                painter.setBrush(
                    QBrush(
                        QColor(
                            20,
                            65,
                            88,
                            255,
                        )
                        if selected
                        else QColor(
                            12,
                            24,
                            36,
                            250,
                        )
                    )
                )

                painter.setPen(
                    QPen(
                        QColor(
                            115,
                            115,
                            120,
                        ),
                        1,
                    )
                )

                painter.drawRect(
                    tab_x,
                    box_y,
                    int(tab_w),
                    tab_h,
                )

                painter.setPen(
                    QColor(
                        0,
                        220,
                        255,
                    )
                    if selected
                    else QColor(
                        205,
                        205,
                        205,
                    )
                )

                painter.drawText(
                    QRectF(
                        tab_x,
                        box_y,
                        tab_w,
                        tab_h,
                    ),
                    Qt.AlignmentFlag.AlignCenter,
                    label,
                )

            content_top = box_y + tab_h

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
        # Range label sits inside the map content, below tabs.
        painter.drawText(
            box_x + 10,
            box_y + 38,
            f"{map_state.range_nm:.0f} NM",
        )

        center_x = box_x + box_w // 2
        center_y = content_top + (box_h - tab_h) // 2

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

        # Label declutter affects text only: every airport marker is still drawn.
        placed_airport_labels: list[tuple[int, int]] = []
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

            # Labels near ownship or previous labels are omitted to keep
            # the 170px inset legible; selected/touched labels always show.
            label_priority = is_selected or is_touch_selected
            away_from_ownship = (
                abs(airport_x - center_x) > 20
                or abs(airport_y - center_y) > 20
            )
            not_colliding = all(
                abs(airport_x - px) >= 29
                or abs(airport_y - py) >= 13
                for px, py in placed_airport_labels
            )
            if label_priority or (away_from_ownship and not_colliding):
                painter.drawText(
                    airport_x + 6,
                    airport_y,
                    airport.ident,
                )
                placed_airport_labels.append((airport_x, airport_y))

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
        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        route = self.route_manager.load_route()
        active_leg = self.route_manager.get_active_leg()

        # GARMIN REDESIGN: structured right-side Active Flight Plan.
        box_x, box_y, box_w, box_h = width - 194, 48, 188, 126

        painter.setBrush(QBrush(QColor(8, 12, 20, 255)))
        painter.setPen(QPen(QColor(115, 115, 120), 1))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QColor(0, 220, 255))
        painter.drawText(
            box_x + 8, box_y + 18,
            "STATIC TEST SCENE" if self._v6_mountain_scene() else "ACTIVE FLIGHT PLAN",
        )

        if self._v6_mountain_scene():
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(box_x + 8, box_y + 43, "NO ACTIVE TEST ROUTE")
            painter.drawText(box_x + 8, box_y + 65, "40.3300 N, 105.5300 W")
            painter.drawText(
                box_x + 8, box_y + 87,
                "LONGS PEAK / 220 DEG" if self._v8_ridge_scene()
                else "LOOKING SW / 240 DEG",
            )
            painter.drawText(box_x + 8, box_y + 109, "NOT FOR FLIGHT")
            return

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))

        route_id = route.get("route_id", "NO ROUTE")
        waypoints = route.get("waypoints", [])

        painter.drawText(box_x + 8, box_y + 39, str(route_id)[:22])

        if waypoints:
            painter.setPen(QColor(255, 0, 255))
            painter.drawText(
                box_x + 8,
                box_y + 60,
                " → ".join(waypoints)[:27],
            )

        if active_leg:
            painter.setPen(QColor(0, 255, 0))
            painter.drawText(
                box_x + 8,
                box_y + 84,
                f"{active_leg.from_ident} → {active_leg.to_ident}",
            )

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                box_x + 8,
                box_y + 105,
                f"DTK {active_leg.desired_track_deg:.0f}°",
            )

    def draw_selected_airport_info(self, painter: QPainter, width: int, height: int) -> None:
        # BLAKE_V6_MOUNTAIN_SCENE_INFO: no Cincinnati airport in mountain mode.
        if self._v6_mountain_scene():
            box_x, box_y, box_w, box_h = width - 194, 180, 188, 142
            painter.save()
            painter.fillRect(box_x, box_y, box_w, box_h, QColor(8, 12, 20, 255))
            painter.setPen(QPen(QColor(115, 115, 120), 1))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawRect(box_x, box_y, box_w, box_h)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(0, 220, 255))
            painter.drawText(box_x + 8, box_y + 18, "SCENE INFO")
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                box_x + 8, box_y + 41,
                ("LONGS PEAK VIEW / 15K MSL" if self._v9_high_ridge_scene()
                 else "LONGS PEAK VIEW / 12K MSL")
                if self._v8_ridge_scene() else "ROCKY MOUNTAINS",
            )
            painter.drawText(box_x + 8, box_y + 63, "REAL SRTM ELEVATION")
            painter.drawText(box_x + 8, box_y + 85, "STATIC GPS POSITION")
            painter.drawText(box_x + 8, box_y + 108, "AIRPORT DATA: N/A")
            painter.restore()
            return
        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        airport_id = self.config.navigation.selected_waypoint_id
        airport = self.database.get_airport(airport_id)

        if airport is None:
            return

        runway = self.database.best_runway(airport_id)
        freqs = self.database.get_frequencies(airport_id)

        # GARMIN REDESIGN: Airport Info below Active Flight Plan.
        box_x = width - 194
        box_y = 180
        box_w = 188
        box_h = 142

        painter.setBrush(QBrush(QColor(8, 12, 20, 255)))
        painter.setPen(QPen(QColor(115, 115, 120), 1))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QColor(0, 220, 255))
        painter.drawText(box_x + 8, box_y + 18, "AIRPORT INFO")

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            box_x + 8,
            box_y + 39,
            f"{airport.ident}  {airport.name[:16]}",
        )
        painter.drawText(
            box_x + 8,
            box_y + 58,
            f"ELEV {airport.elevation_ft:.0f} FT",
        )

        if runway:
            painter.drawText(
                box_x + 8,
                box_y + 78,
                f"RWY {runway.le_ident}/{runway.he_ident}",
            )
            painter.drawText(
                box_x + 8,
                box_y + 96,
                f"{runway.length_ft:.0f} x {runway.width_ft:.0f} FT",
            )

        y = box_y + 117
        for freq in freqs[:1]:
            painter.setPen(QColor(0, 220, 255))
            painter.drawText(
                box_x + 8,
                y,
                f"{freq.type} {freq.frequency_mhz:.3f}",
            )

    def draw_startup_status_box(self, painter: QPainter, width: int, height: int) -> None:
        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        status = self.startup_status

        if (
            status.database_ok
            and status.config_ok
        ):
            return

        box_x = 20
        box_y = 20
        box_w = 280
        box_h = 65

        # Startup failure must remain readable over
        # any synthetic-vision background.
        painter.fillRect(
            box_x,
            box_y,
            box_w,
            box_h,
            QColor(
                0,
                0,
                0,
                225,
            ),
        )


        color = QColor(0, 255, 0) if status.database_ok and status.config_ok else QColor(255, 0, 0)

        painter.setPen(QPen(color, 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 10, box_y + 24, status.status_text)

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 50, f"APT {status.airports_loaded}  NAV {status.navaids_loaded}")

    def draw_sensor_status_panel(self, painter: QPainter, width: int, height: int) -> None:
        # PFD_HIDE_SIM_SENSOR_PANEL
        if not self.use_hardware:
            return

        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        box_x = 310
        box_y = 20
        box_w = 300
        box_h = 90

        status = getattr(
            self.sensors,
            "status",
            None,
        )

        sensor_problem = (
            status is None
            or not all(
                (
                    bool(
                        getattr(
                            status,
                            "bno085_ok",
                            False,
                        )
                    ),
                    bool(
                        getattr(
                            status,
                            "baro_ok",
                            False,
                        )
                    ),
                    bool(
                        getattr(
                            status,
                            "airspeed_ok",
                            False,
                        )
                    ),
                    bool(
                        getattr(
                            status,
                            "gps_ok",
                            False,
                        )
                    ),
                )
            )
        )

        if sensor_problem:
            painter.fillRect(
                box_x,
                box_y,
                box_w,
                box_h,
                QColor(
                    0,
                    0,
                    0,
                    225,
                ),
            )

        border_color = (
            QColor(
                255,
                0,
                0,
            )
            if sensor_problem
            else QColor(
                255,
                255,
                255,
            )
        )

        painter.setPen(
            QPen(
                border_color,
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
                11,
                QFont.Weight.Bold,
            )
        )

        mode_text = (
            "HARDWARE"
            if self.use_hardware
            else "SIM"
        )

        painter.setPen(
            QColor(
                255,
                0,
                0,
            )
            if sensor_problem
            else QColor(
                0,
                255,
                0,
            )
        )
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
        # PFD_HIDE_SIM_PROFILE
        return

        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        if self.use_hardware:
            return

        profile = self.config.simulation.profile.upper()

        box_x = 620
        box_y = 20
        box_w = 230
        box_h = 65

        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 255))
        painter.drawText(box_x + 10, box_y + 25, "SIM PROFILE")

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(box_x + 10, box_y + 50, profile)

    def draw_terrain_status_box(self, painter: QPainter, terrain_state, width: int, height: int) -> None:
        # A dedicated status row between engine gauges and the local map.
        # BLAKE_V6_SRTM_STATUS: never label legacy fallback's ~700 ft as SRTM.
        box_x, box_y, box_w, box_h = 10, 275, 160, 29
        v6_srtm = self._v6_demo_scene() and self.real_terrain_enabled
        real_sample = self._v6_current_srtm_status() if v6_srtm else None
        if v6_srtm:
            # Neutral presentation: alert severity is computed independently
            # by the real-terrain safety pipeline; this is GND-at-GPS only.
            color = QColor(0, 205, 230) if real_sample is not None else QColor(255, 220, 0)
            source_label = "SRTM AT GPS"
            if real_sample is None:
                detail_text = "GND NO DATA  AGL --"
            else:
                ground_ft, agl_ft = real_sample
                detail_text = f"GND {ground_ft:.0f} FT AGL {agl_ft:.0f} FT"
        else:
            if terrain_state.warning_level == "red":
                color = QColor(255, 40, 40)
            elif terrain_state.warning_level == "yellow" or not self.real_terrain_enabled:
                color = QColor(255, 220, 0)
            else:
                color = QColor(0, 220, 130)
            source_label = "SRTM" if self.real_terrain_enabled else "FALLBACK"
            detail_text = (
                f"ELEV {terrain_state.terrain_elevation_ft:.0f} FT  "
                f"CLR {terrain_state.clearance_ft:.0f} FT"
            )

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(4, 8, 14, 245))
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawRect(box_x, box_y, box_w, box_h)
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 5, box_y + 12, f"TERRAIN [{source_label}]")
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        painter.setPen(QColor(240, 240, 240))
        painter.drawText(box_x + 5, box_y + 25, detail_text)


    def draw_terrain_alert(self, painter: QPainter, terrain_state, width: int, height: int) -> None:
        if terrain_state.warning_level == "none":
            return

        color = QColor(255, 0, 0) if terrain_state.warning_level == "red" else QColor(255, 220, 0)

        painter.setPen(QPen(color, 3))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 55, width, 40), Qt.AlignmentFlag.AlignCenter, f"TERRAIN {terrain_state.clearance_ft:.0f} FT")

    def draw_obstacle_overlay(
        self,
        painter: QPainter,
        obstacle_state,
        width: int,
        height: int,
    ) -> None:
        # This row no longer covers the map or the terrain status.
        box_x, box_y, box_w, box_h = 10, 309, 160, 30
        if not obstacle_state.ok:
            color = QColor(255, 180, 0)
            title = "OBST DATA"
            detail = "UNAVAILABLE"
        elif not obstacle_state.nearby:
            return
        else:
            color = (
                QColor(255, 0, 0) if obstacle_state.warning
                else QColor(255, 220, 0)
            )
            obstacle = obstacle_state.nearby[0]
            title = "OBSTACLE"
            detail = (
                f"{obstacle.ident[:10]}  {obstacle.distance_nm:.1f}NM"
                f"  {obstacle.bearing_deg:.0f}°"
            )

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(4, 8, 14, 245))
        painter.setPen(QPen(color, 1))
        if hasattr(painter, "setBrush"):
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawRect(box_x, box_y, box_w, box_h)
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(box_x + 5, box_y + 12, title)
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        painter.drawText(box_x + 5, box_y + 26, detail)


    def draw_safe_taxi_map(
        self,
        painter: QPainter,
        taxi_state,
        width: int,
        height: int,
    ) -> None:
        painter.fillRect(
            0,
            0,
            width,
            height,
            QColor(15, 15, 15),
        )

        painter.setPen(
            QPen(
                QColor(255, 255, 255),
                2,
            )
        )
        painter.setFont(
            QFont(
                "Arial",
                22,
                QFont.Weight.Bold,
            )
        )
        painter.drawText(
            30,
            45,
            (
                "SAFE TAXI - "
                f"{taxi_state.airport_id}"
            ),
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Weight.Bold,
            )
        )
        painter.setPen(
            QColor(
                255,
                180,
                0,
            )
        )
        painter.drawText(
            30,
            68,
            "RUNWAY-ONLY SURFACE VIEW",
        )

        if self.pfd is None:
            painter.drawText(
                30,
                95,
                "POSITION DATA UNAVAILABLE",
            )
            return

        runway_records = (
            self.database.get_runways(
                taxi_state.airport_id
            )
        )

        runway_geometries = []

        for runway in runway_records:
            geometry = (
                self.runway_geometry_computer.compute(
                    runway=runway,
                    aircraft_lat_deg=(
                        self.pfd.latitude_deg
                    ),
                    aircraft_lon_deg=(
                        self.pfd.longitude_deg
                    ),
                    aircraft_alt_ft=(
                        self.pfd.indicated_alt_ft
                    ),
                )
            )

            if geometry is not None:
                runway_geometries.append(
                    geometry
                )

        projection = (
            self.safe_taxi_projector.project(
                runways=runway_geometries,
                heading_deg=(
                    taxi_state.heading_deg
                ),
                width_px=width,
                height_px=height,
            )
        )

        if not projection.valid:
            painter.setPen(
                QColor(
                    255,
                    180,
                    0,
                )
            )
            painter.drawText(
                30,
                95,
                "SURFACE DATA UNAVAILABLE",
            )
            return

        if not projection.runways:
            painter.setPen(
                QColor(
                    255,
                    180,
                    0,
                )
            )
            painter.drawText(
                30,
                95,
                "RUNWAY DATA UNAVAILABLE",
            )

        for runway in projection.runways:
            polygon = QPolygonF(
                [
                    QPointF(
                        point.x,
                        point.y,
                    )
                    for point in runway.corners
                ]
            )

            painter.setBrush(
                QBrush(
                    QColor(
                        70,
                        70,
                        70,
                    )
                )
            )
            painter.setPen(
                QPen(
                    QColor(
                        235,
                        235,
                        235,
                    ),
                    2,
                )
            )
            painter.drawPolygon(
                polygon
            )

            painter.setPen(
                QPen(
                    QColor(
                        255,
                        255,
                        255,
                    ),
                    1,
                    Qt.PenStyle.DashLine,
                )
            )
            painter.drawLine(
                QPointF(
                    runway.low_center_x,
                    runway.low_center_y,
                ),
                QPointF(
                    runway.high_center_x,
                    runway.high_center_y,
                ),
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

            if runway.low_ident:
                painter.drawText(
                    QPointF(
                        runway.low_center_x + 8,
                        runway.low_center_y - 8,
                    ),
                    runway.low_ident,
                )

            if runway.high_ident:
                painter.drawText(
                    QPointF(
                        runway.high_center_x + 8,
                        runway.high_center_y - 8,
                    ),
                    runway.high_ident,
                )

        # Heading-up display: ownship stays fixed and
        # points toward the top of the screen.
        ownship_x = projection.ownship_x
        ownship_y = projection.ownship_y

        ownship = QPolygonF(
            [
                QPointF(
                    ownship_x,
                    ownship_y - 18,
                ),
                QPointF(
                    ownship_x - 12,
                    ownship_y + 14,
                ),
                QPointF(
                    ownship_x,
                    ownship_y + 8,
                ),
                QPointF(
                    ownship_x + 12,
                    ownship_y + 14,
                ),
            ]
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
        painter.drawPolygon(
            ownship
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
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
            30,
            height - 52,
            (
                f"HDG "
                f"{taxi_state.heading_deg % 360.0:03.0f}°"
            ),
        )

        if (
            taxi_state.airport_distance_nm
            is not None
        ):
            painter.drawText(
                30,
                height - 30,
                (
                    f"AIRPORT "
                    f"{taxi_state.airport_distance_nm:.2f} NM"
                ),
            )

        painter.drawText(
            width - 170,
            height - 30,
            "RANGE 3500 FT",
        )

    def _read_stratux_weather_states(
        self,
    ):
        """
        Perform exactly one Stratux UDP read and
        distribute that same receiver state to the
        traffic and weather subsystems.
        """

        stratux_state = (
            self.stratux.read()
        )

        self.weather.ingest_uplinks(
            getattr(
                stratux_state,
                "uplinks",
                None,
            )
            or []
        )

        weather_state = (
            self.weather.read()
        )

        return (
            stratux_state,
            weather_state,
        )

    def draw_traffic_overlay(
        self,
        painter: QPainter,
        stratux_state,
        width: int,
        height: int,
    ) -> None:
        """
        Draw validated Stratux traffic over the
        lower-left local map.

        Traffic is suppressed when Stratux data or
        ownship GPS position is not fresh.

        ADS-B pressure altitude is compared only
        against ownship pressure altitude.
        """

        del width, height

        painter.save()

        try:
            # GARMIN REDESIGN:
            # Shared TRAFFIC / WEATHER / MAP pane geometry.
            box_x = 5
            box_y = 350
            box_w = 170
            box_h = 215

            tab_h = 22
            plot_y = box_y + tab_h
            plot_h = box_h - tab_h

            center_x = (
                box_x
                + box_w / 2.0
            )

            center_y = (
                plot_y
                + plot_h / 2.0
            )

            radius = (
                min(
                    box_w,
                    plot_h,
                )
                * 0.42
            )

            # Compact receiver status.
            painter.setFont(
                QFont(
                    "Arial",
                    8,
                    QFont.Weight.Bold,
                )
            )

            painter.setPen(
                QColor(
                    0,
                    255,
                    255,
                )
                if stratux_state.ok
                else QColor(
                    255,
                    180,
                    0,
                )
            )

            painter.drawText(
                108,
                535,
                (
                    "TFC ON"
                    if stratux_state.ok
                    else "TFC OFF"
                ),
            )

            # Fail closed:
            # no traffic symbols without fresh
            # valid receiver data.
            if not stratux_state.ok:
                return

            targets = (
                stratux_state.traffic
                or []
            )

            if not targets:
                return

            pfd = getattr(
                self,
                "pfd",
                None,
            )

            watchdog = getattr(
                self,
                "sensor_watchdog_state",
                None,
            )

            if (
                pfd is None
                or watchdog is None
            ):
                return

            if not bool(
                getattr(
                    pfd,
                    "position_valid",
                    False,
                )
            ):
                return

            if not bool(
                getattr(
                    watchdog,
                    "position_valid",
                    False,
                )
            ):
                return

            if not bool(
                getattr(
                    watchdog,
                    "position_fresh",
                    False,
                )
            ):
                return

            own_lat = getattr(
                pfd,
                "latitude_deg",
                None,
            )

            own_lon = getattr(
                pfd,
                "longitude_deg",
                None,
            )

            # Only use ownship pressure altitude
            # for traffic relative-altitude labels
            # when air data is valid and fresh.
            air_data_usable = bool(
                getattr(
                    watchdog,
                    "air_data_valid",
                    False,
                )
                and getattr(
                    watchdog,
                    "air_data_fresh",
                    False,
                )
            )

            if air_data_usable:
                own_pressure_alt = getattr(
                    pfd,
                    "pressure_alt_ft",
                    None,
                )
            else:
                own_pressure_alt = None

            map_range_nm = getattr(
                self,
                "map_range_nm",
                None,
            )

            try:
                map_range_nm = float(
                    map_range_nm
                )
            except (
                TypeError,
                ValueError,
            ):
                return

            if (
                not isfinite(
                    map_range_nm
                )
                or map_range_nm <= 0.0
            ):
                return

            orientation_state = getattr(
                self,
                "map_orientation_state",
                None,
            )

            reference_deg = getattr(
                orientation_state,
                "reference_deg",
                0.0,
            )

            try:
                reference_deg = float(
                    reference_deg
                )
            except (
                TypeError,
                ValueError,
            ):
                reference_deg = 0.0

            if not isfinite(
                reference_deg
            ):
                reference_deg = 0.0

            visible = []

            for target in targets:

                if not bool(
                    getattr(
                        target,
                        "position_valid",
                        False,
                    )
                ):
                    continue

                geometry = (
                    calculate_traffic_geometry(
                        own_lat_deg=own_lat,
                        own_lon_deg=own_lon,
                        own_pressure_alt_ft=(
                            own_pressure_alt
                        ),
                        target_lat_deg=getattr(
                            target,
                            "latitude_deg",
                            None,
                        ),
                        target_lon_deg=getattr(
                            target,
                            "longitude_deg",
                            None,
                        ),
                        target_pressure_alt_ft=getattr(
                            target,
                            "pressure_alt_ft",
                            None,
                        ),
                    )
                )

                if geometry is None:
                    continue

                if (
                    geometry.distance_nm
                    > map_range_nm
                ):
                    continue

                visible.append(
                    (
                        bool(
                            getattr(
                                target,
                                "traffic_alert",
                                False,
                            )
                        ),
                        geometry.distance_nm,
                        target,
                        geometry,
                    )
                )

            # Alerts first, then nearest targets.
            visible.sort(
                key=lambda item: (
                    not item[0],
                    item[1],
                )
            )

            # Keep the small PFD map readable.
            visible = visible[:8]

            painter.setBrush(
                QBrush(
                    Qt.BrushStyle.NoBrush
                )
            )

            for (
                alert,
                _distance_nm,
                target,
                geometry,
            ) in visible:

                relative_bearing = (
                    geometry.bearing_deg
                    - reference_deg
                ) % 360.0

                angle = radians(
                    relative_bearing
                )

                target_radius = (
                    radius
                    * min(
                        1.0,
                        geometry.distance_nm
                        / map_range_nm,
                    )
                )

                x = (
                    center_x
                    + sin(angle)
                    * target_radius
                )

                y = (
                    center_y
                    - cos(angle)
                    * target_radius
                )

                color = (
                    QColor(
                        255,
                        220,
                        0,
                    )
                    if alert
                    else QColor(
                        0,
                        255,
                        255,
                    )
                )

                painter.setPen(
                    QPen(
                        color,
                        2,
                    )
                )

                size = (
                    6.0
                    if alert
                    else 5.0
                )

                # Hollow diamond traffic symbol.
                painter.drawPolygon(
                    QPolygonF(
                        [
                            QPointF(
                                x,
                                y - size,
                            ),
                            QPointF(
                                x + size,
                                y,
                            ),
                            QPointF(
                                x,
                                y + size,
                            ),
                            QPointF(
                                x - size,
                                y,
                            ),
                        ]
                    )
                )

                painter.setFont(
                    QFont(
                        "Arial",
                        7,
                        QFont.Weight.Bold,
                    )
                )

                if (
                    geometry.relative_alt_ft
                    is None
                ):
                    altitude_text = "---"
                else:
                    relative_hundreds = int(
                        round(
                            geometry.relative_alt_ft
                            / 100.0
                        )
                    )

                    altitude_text = (
                        f"{relative_hundreds:+03d}"
                    )

                vertical_speed = getattr(
                    target,
                    "vertical_speed_fpm",
                    None,
                )

                trend_text = ""

                if (
                    vertical_speed
                    is not None
                ):
                    try:
                        vertical_speed = float(
                            vertical_speed
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        vertical_speed = None

                if (
                    vertical_speed is not None
                    and isfinite(
                        vertical_speed
                    )
                ):
                    if vertical_speed >= 500.0:
                        trend_text = "↑"
                    elif vertical_speed <= -500.0:
                        trend_text = "↓"

                painter.setPen(
                    color
                )

                painter.drawText(
                    int(x + 7),
                    int(y - 1),
                    (
                        altitude_text
                        + trend_text
                    ),
                )

                # Callsign only for a GDL90
                # traffic-alert target to avoid
                # excessive map clutter.
                if alert:
                    callsign = str(
                        getattr(
                            target,
                            "callsign",
                            "",
                        )
                    ).strip()

                    if callsign:
                        painter.drawText(
                            int(x + 7),
                            int(y + 10),
                            callsign[:7],
                        )

        finally:
            painter.restore()

    def draw_weather_overlay(
        self,
        painter: QPainter,
        weather_state,
        width: int,
        height: int,
    ) -> None:
        """
        Draw fresh FIS-B NEXRAD underneath traffic
        in the lower-left local map.

        Radar plotting fails closed without fresh
        ownship position.

        FIS-B levels 0/1 are intentionally not
        painted. Higher precipitation levels use
        progressively stronger colors.
        """

        del width, height

        painter.save()

        try:
            # Must remain synchronized with the
            # local moving-map / traffic geometry.
            # GARMIN REDESIGN: synchronized MAP / WEATHER pane.
            box_x = 5
            box_y = 350
            box_w = 170
            box_h = 215

            tab_h = 22
            plot_y = box_y + tab_h
            plot_h = box_h - tab_h

            center_x = (
                box_x
                + box_w / 2.0
            )

            center_y = (
                plot_y
                + plot_h / 2.0
            )

            radius = (
                min(
                    box_w,
                    plot_h,
                )
                * 0.42
            )

            pfd = getattr(
                self,
                "pfd",
                None,
            )

            watchdog = getattr(
                self,
                "sensor_watchdog_state",
                None,
            )

            position_usable = bool(
                pfd is not None
                and watchdog is not None
                and getattr(
                    pfd,
                    "position_valid",
                    False,
                )
                and getattr(
                    watchdog,
                    "position_valid",
                    False,
                )
                and getattr(
                    watchdog,
                    "position_fresh",
                    False,
                )
            )

            weather_ok = bool(
                getattr(
                    weather_state,
                    "ok",
                    False,
                )
            )

            painter.setFont(
                QFont(
                    "Arial",
                    8,
                    QFont.Weight.Bold,
                )
            )

            if weather_ok:
                if position_usable:
                    painter.setPen(
                        QColor(
                            0,
                            255,
                            0,
                        )
                    )

                    status_text = "WX ON"
                else:
                    painter.setPen(
                        QColor(
                            255,
                            180,
                            0,
                        )
                    )

                    status_text = "WX POS"
            else:
                painter.setPen(
                    QColor(
                        255,
                        180,
                        0,
                    )
                )

                status_text = "WX WAIT"

            painter.drawText(
                108,
                549,
                status_text,
            )

            if (
                not weather_ok
                or not position_usable
            ):
                return

            blocks = (
                getattr(
                    weather_state,
                    "nexrad_blocks",
                    None,
                )
                or []
            )

            if not blocks:
                return

            own_lat = getattr(
                pfd,
                "latitude_deg",
                None,
            )

            own_lon = getattr(
                pfd,
                "longitude_deg",
                None,
            )

            map_range_nm = getattr(
                self,
                "map_range_nm",
                None,
            )

            try:
                map_range_nm = float(
                    map_range_nm
                )
            except (
                TypeError,
                ValueError,
            ):
                return

            if (
                not isfinite(
                    map_range_nm
                )
                or map_range_nm <= 0.0
            ):
                return

            orientation_state = getattr(
                self,
                "map_orientation_state",
                None,
            )

            reference_deg = getattr(
                orientation_state,
                "reference_deg",
                0.0,
            )

            try:
                reference_deg = float(
                    reference_deg
                )
            except (
                TypeError,
                ValueError,
            ):
                reference_deg = 0.0

            if not isfinite(
                reference_deg
            ):
                reference_deg = 0.0

            def project_point(
                latitude_deg,
                longitude_deg,
            ):
                geometry = (
                    calculate_traffic_geometry(
                        own_lat_deg=own_lat,
                        own_lon_deg=own_lon,
                        own_pressure_alt_ft=None,
                        target_lat_deg=(
                            latitude_deg
                        ),
                        target_lon_deg=(
                            longitude_deg
                        ),
                        target_pressure_alt_ft=None,
                    )
                )

                if geometry is None:
                    return None

                relative_bearing = (
                    geometry.bearing_deg
                    - reference_deg
                ) % 360.0

                angle = radians(
                    relative_bearing
                )

                # Do NOT clamp weather to the edge.
                # Off-range polygons are clipped out.
                point_radius = (
                    radius
                    * geometry.distance_nm
                    / map_range_nm
                )

                return QPointF(
                    center_x
                    + sin(angle)
                    * point_radius,
                    center_y
                    - cos(angle)
                    * point_radius,
                )

            # Radar must stay inside the local map.
            painter.setClipRect(
                box_x,
                box_y,
                box_w,
                box_h,
            )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            # Draw coarse CONUS data first and
            # higher-detail regional data afterward.
            #
            # Scale 2 = coarsest, scale 0 = finest.
            ordered_blocks = sorted(
                blocks,
                key=lambda block: (
                    0
                    if int(
                        getattr(
                            block,
                            "product_id",
                            0,
                        )
                    ) == 64
                    else 1,
                    -int(
                        getattr(
                            block,
                            "scale_factor",
                            0,
                        )
                    ),
                ),
            )

            color_by_level = {
                2: QColor(
                    0,
                    170,
                    0,
                    115,
                ),
                3: QColor(
                    0,
                    230,
                    0,
                    135,
                ),
                4: QColor(
                    255,
                    220,
                    0,
                    150,
                ),
                5: QColor(
                    255,
                    140,
                    0,
                    165,
                ),
                6: QColor(
                    255,
                    0,
                    0,
                    180,
                ),
                7: QColor(
                    220,
                    0,
                    220,
                    195,
                ),
            }

            for block in ordered_blocks:

                intensity = tuple(
                    getattr(
                        block,
                        "intensity",
                        (),
                    )
                )

                if len(
                    intensity
                ) != 128:
                    continue

                lat_north = float(
                    block.lat_north_deg
                )

                lon_west = float(
                    block.lon_west_deg
                )

                block_height = float(
                    block.height_deg
                )

                block_width = float(
                    block.width_deg
                )

                values = (
                    lat_north,
                    lon_west,
                    block_height,
                    block_width,
                )

                if not all(
                    isfinite(value)
                    for value
                    in values
                ):
                    continue

                if (
                    block_height <= 0.0
                    or block_width <= 0.0
                ):
                    continue

                # Cheap geographic rejection before
                # projecting all 165 grid vertices.
                block_center_lat = (
                    lat_north
                    - block_height / 2.0
                )

                block_center_lon = (
                    lon_west
                    + block_width / 2.0
                )

                center_geometry = (
                    calculate_traffic_geometry(
                        own_lat_deg=own_lat,
                        own_lon_deg=own_lon,
                        own_pressure_alt_ft=None,
                        target_lat_deg=(
                            block_center_lat
                        ),
                        target_lon_deg=(
                            block_center_lon
                        ),
                        target_pressure_alt_ft=None,
                    )
                )

                if center_geometry is None:
                    continue

                # Conservative margin. Degrees are
                # multiplied by 60 NM/degree so we
                # never reject a potentially visible
                # block merely for optimization.
                block_margin_nm = (
                    max(
                        block_height,
                        block_width,
                    )
                    * 60.0
                )

                if (
                    center_geometry.distance_nm
                    > (
                        map_range_nm
                        + block_margin_nm
                    )
                ):
                    continue

                cell_height = (
                    block_height
                    / 4.0
                )

                cell_width = (
                    block_width
                    / 32.0
                )

                # Project the 5 x 33 grid once.
                # Each of the 128 cells reuses these
                # vertices rather than performing
                # four geographic calculations.
                grid = []

                grid_valid = True

                for row in range(5):
                    grid_row = []

                    latitude = (
                        lat_north
                        - row
                        * cell_height
                    )

                    for column in range(
                        33
                    ):
                        longitude = (
                            lon_west
                            + column
                            * cell_width
                        )

                        point = project_point(
                            latitude,
                            longitude,
                        )

                        if point is None:
                            grid_valid = False
                            break

                        grid_row.append(
                            point
                        )

                    if not grid_valid:
                        break

                    grid.append(
                        grid_row
                    )

                if not grid_valid:
                    continue

                for row in range(4):
                    for column in range(
                        32
                    ):
                        level = int(
                            intensity[
                                column
                                + row * 32
                            ]
                        )

                        # Levels 0/1 are suppressed.
                        # In particular, Stratux uses
                        # level 1 for CONUS empty-block
                        # representation.
                        color = (
                            color_by_level.get(
                                level
                            )
                        )

                        if color is None:
                            continue

                        painter.setBrush(
                            QBrush(
                                color
                            )
                        )

                        painter.drawPolygon(
                            QPolygonF(
                                [
                                    grid[
                                        row
                                    ][
                                        column
                                    ],
                                    grid[
                                        row
                                    ][
                                        column + 1
                                    ],
                                    grid[
                                        row + 1
                                    ][
                                        column + 1
                                    ],
                                    grid[
                                        row + 1
                                    ][
                                        column
                                    ],
                                ]
                            )
                        )

        finally:
            painter.restore()

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




    def draw_compact_engine_overlay(
        self,
        painter: QPainter,
        x: int,
        y: int,
        width: int,
    ) -> None:
        """Always-visible transparent PFD engine strip."""

        painter.save()

        try:
            painter.setBrush(
                QBrush(
                    Qt.BrushStyle.NoBrush
                )
            )

            engine_state = getattr(
                self,
                "engine_state",
                None,
            )

            if engine_state is None:
                aircraft = getattr(
                    self,
                    "aircraft",
                    None,
                )

                engine_state = getattr(
                    aircraft,
                    "engine_state",
                    None,
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
                    0,
                    220,
                    255,
                )
            )

            # When the urgent 72 px banner is visible, only this decorative
            # heading is skipped in the V14 demo, not ANY numeric engine row.
            # Moving it downward would collide with RPM, so don't do that.
            v14_banner_over_engine_title = (
                self._v14_cincinnati_profile_enabled()
                and getattr(getattr(self, "terrain_warning_presentation", None),
                            "visible", False)
            )
            if not v14_banner_over_engine_title:
                painter.drawText(x, y + 14, "ENGINE")
                painter.drawLine(x, y + 20, x + width, y + 20)

            if engine_state is None:
                painter.setPen(
                    QColor(
                        255,
                        180,
                        0,
                    )
                )

                painter.drawText(
                    x,
                    y + 42,
                    "ENGINE DATA ---",
                )

                return

            engine = engine_state.data

            sensor_status = getattr(
                self,
                "engine_sensor_status",
                None,
            )

            def channel_usable(name):
                if sensor_status is None:
                    return True

                status = getattr(
                    sensor_status,
                    name,
                    None,
                )

                if status is None:
                    return True

                return bool(
                    status.valid
                    and status.fresh
                )

            def unavailable():
                return QColor(
                    255,
                    80,
                    80,
                )

            def text_for(
                value,
                decimals=0,
                unit="",
                usable=True,
                signed=False,
            ):
                if not usable:
                    return (
                        f"--- {unit}".rstrip()
                    )

                if signed:
                    value_text = (
                        f"{value:+.{decimals}f}"
                    )
                else:
                    value_text = (
                        f"{value:.{decimals}f}"
                    )

                if unit:
                    return (
                        f"{value_text} {unit}"
                    )

                return value_text

            rpm_ok = channel_usable(
                "rpm"
            )
            oil_p_ok = channel_usable(
                "oil_pressure"
            )
            oil_t_ok = channel_usable(
                "oil_temperature"
            )
            fuel_p_ok = channel_usable(
                "fuel_pressure"
            )
            fuel_flow_ok = channel_usable(
                "fuel_flow"
            )
            volts_ok = channel_usable(
                "volts"
            )
            amps_ok = channel_usable(
                "amps"
            )

            rpm_color = (
                self.ems_page.rpm_color(
                    engine.rpm
                )
                if rpm_ok
                else unavailable()
            )

            oil_p_color = (
                self.ems_page
                .oil_pressure_color(
                    engine.oil_pressure_psi,
                    engine.rpm,
                )
                if oil_p_ok
                else unavailable()
            )

            oil_t_color = (
                self.ems_page
                .oil_temp_color(
                    engine.oil_temp_f
                )
                if oil_t_ok
                else unavailable()
            )

            volts_color = (
                self.ems_page
                .voltage_color(
                    engine.volts
                )
                if volts_ok
                else unavailable()
            )

            normal = QColor(
                255,
                255,
                255,
            )

            rows = [
                (
                    "RPM",
                    text_for(
                        engine.rpm,
                        usable=rpm_ok,
                    ),
                    rpm_color,
                ),
                (
                    "OIL PSI",
                    text_for(
                        engine.oil_pressure_psi,
                        usable=oil_p_ok,
                    ),
                    oil_p_color,
                ),
                (
                    "OIL TEMP",
                    text_for(
                        engine.oil_temp_f,
                        unit="°F",
                        usable=oil_t_ok,
                    ),
                    oil_t_color,
                ),
                (
                    "FUEL PSI",
                    text_for(
                        engine.fuel_pressure_psi,
                        decimals=1,
                        usable=fuel_p_ok,
                    ),
                    (
                        normal
                        if fuel_p_ok
                        else unavailable()
                    ),
                ),
                (
                    "FLOW",
                    text_for(
                        engine.fuel_flow_gph,
                        decimals=1,
                        unit="GPH",
                        usable=fuel_flow_ok,
                    ),
                    (
                        normal
                        if fuel_flow_ok
                        else unavailable()
                    ),
                ),
                (
                    "FUEL",
                    text_for(
                        engine.fuel_remaining_gal,
                        decimals=1,
                        unit="GAL",
                    ),
                    self.ems_page.fuel_color(
                        engine
                    ),
                ),
                (
                    "VOLTS",
                    text_for(
                        engine.volts,
                        decimals=1,
                        unit="V",
                        usable=volts_ok,
                    ),
                    volts_color,
                ),
                (
                    "AMPS",
                    text_for(
                        engine.amps,
                        decimals=1,
                        unit="A",
                        usable=amps_ok,
                        signed=True,
                    ),
                    (
                        normal
                        if amps_ok
                        else unavailable()
                    ),
                ),
            ]

            # GARMIN REFERENCE:
            # Dense vertical engine strip with room beneath for fuel gauge.
            row_y = y + 25
            row_h = 16

            painter.setFont(
                QFont(
                    "Arial",
                    8,
                    QFont.Weight.Bold,
                )
            )

            for label, value, color in rows:
                painter.setPen(
                    QColor(
                        210,
                        210,
                        210,
                    )
                )

                painter.drawText(
                    QRectF(
                        x,
                        row_y,
                        width * 0.50,
                        row_h,
                    ),
                    (
                        Qt.AlignmentFlag
                        .AlignLeft
                        | Qt.AlignmentFlag
                        .AlignVCenter
                    ),
                    label,
                )

                painter.setPen(
                    color
                )

                painter.drawText(
                    QRectF(
                        x + width * 0.43,
                        row_y,
                        width * 0.57,
                        row_h,
                    ),
                    (
                        Qt.AlignmentFlag
                        .AlignRight
                        | Qt.AlignmentFlag
                        .AlignVCenter
                    ),
                    value,
                )

                row_y += row_h

            def hottest(
                values,
                statuses,
            ):
                usable_values = []

                for index, value in enumerate(
                    values or []
                ):
                    if (
                        statuses is not None
                        and index < len(statuses)
                    ):
                        status = statuses[index]

                        if not (
                            status.valid
                            and status.fresh
                        ):
                            continue

                    usable_values.append(
                        float(value)
                    )

                if not usable_values:
                    return None

                return max(
                    usable_values
                )

            cht_statuses = (
                getattr(
                    sensor_status,
                    "cht",
                    None,
                )
                if sensor_status is not None
                else None
            )

            egt_statuses = (
                getattr(
                    sensor_status,
                    "egt",
                    None,
                )
                if sensor_status is not None
                else None
            )

            max_cht = hottest(
                getattr(
                    engine,
                    "cht_f",
                    [],
                ),
                cht_statuses,
            )

            max_egt = hottest(
                getattr(
                    engine,
                    "egt_f",
                    [],
                ),
                egt_statuses,
            )

            for label, value, color_func in (
                (
                    "CHT MAX",
                    max_cht,
                    self.ems_page.cht_color,
                ),
                (
                    "EGT MAX",
                    max_egt,
                    self.ems_page.egt_color,
                ),
            ):
                painter.setPen(
                    QColor(
                        210,
                        210,
                        210,
                    )
                )

                painter.drawText(
                    QRectF(
                        x,
                        row_y,
                        width * 0.50,
                        row_h,
                    ),
                    (
                        Qt.AlignmentFlag
                        .AlignLeft
                        | Qt.AlignmentFlag
                        .AlignVCenter
                    ),
                    label,
                )

                if value is None:
                    painter.setPen(
                        unavailable()
                    )
                    value_text = "---"
                else:
                    painter.setPen(
                        color_func(
                            value
                        )
                    )
                    value_text = (
                        f"{value:.0f}°F"
                    )

                painter.drawText(
                    QRectF(
                        x + width * 0.43,
                        row_y,
                        width * 0.57,
                        row_h,
                    ),
                    (
                        Qt.AlignmentFlag
                        .AlignRight
                        | Qt.AlignmentFlag
                        .AlignVCenter
                    ),
                    value_text,
                )

                row_y += row_h

            # ------------------------------------------------
            # GARMIN REFERENCE: fuel quantity gauge.
            # Existing fuel_remaining_gal remains the source of
            # truth and existing EMS fuel_color() drives warning
            # coloration.
            # ------------------------------------------------
            fuel_value = max(
                0.0,
                float(
                    getattr(
                        engine,
                        "fuel_remaining_gal",
                        0.0,
                    )
                ),
            )

            # Display scale only. This does not alter fuel
            # calculations or alert logic.
            fuel_scale_max = max(
                20.0,
                fuel_value,
            )

            fuel_ratio = max(
                0.0,
                min(
                    1.0,
                    fuel_value / fuel_scale_max,
                ),
            )

            gauge_x = x
            gauge_y = row_y + 5
            gauge_w = width
            gauge_h = 34

            painter.setPen(
                QPen(
                    QColor(
                        110,
                        110,
                        115,
                    ),
                    1,
                )
            )

            painter.setBrush(
                QBrush(
                    QColor(
                        0,
                        0,
                        0,
                        175,
                    )
                )
            )

            painter.drawRect(
                gauge_x,
                gauge_y,
                gauge_w,
                gauge_h,
            )

            painter.setPen(
                QColor(
                    200,
                    200,
                    200,
                )
            )

            painter.setFont(
                QFont(
                    "Arial",
                    7,
                    QFont.Weight.Bold,
                )
            )

            painter.drawText(
                gauge_x + 4,
                gauge_y + 11,
                "FUEL QTY",
            )

            bar_x = gauge_x + 4
            bar_y = gauge_y + 17
            bar_w = max(
                10,
                gauge_w - 8,
            )
            bar_h = 10

            painter.setBrush(
                QBrush(
                    QColor(
                        35,
                        35,
                        38,
                    )
                )
            )

            painter.setPen(
                QPen(
                    QColor(
                        100,
                        100,
                        105,
                    ),
                    1,
                )
            )

            painter.drawRect(
                bar_x,
                bar_y,
                bar_w,
                bar_h,
            )

            fill_w = int(
                max(
                    0,
                    bar_w - 2,
                )
                * fuel_ratio
            )

            painter.setBrush(
                QBrush(
                    self.ems_page.fuel_color(
                        engine
                    )
                )
            )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.drawRect(
                bar_x + 1,
                bar_y + 1,
                fill_w,
                max(
                    1,
                    bar_h - 2,
                ),
            )

            painter.setPen(
                self.ems_page.fuel_color(
                    engine
                )
            )

            painter.drawText(
                QRectF(
                    gauge_x,
                    gauge_y,
                    gauge_w - 4,
                    14,
                ),
                (
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                ),
                f"{fuel_value:.1f} GAL",
            )

        finally:
            painter.restore()


    def draw_aircraft_state_label(
        self,
        painter: QPainter,
        width: int,
        height: int,
    ) -> None:
        # GARMIN REDESIGN:
        # Legacy phase/checklist overlay occupied the same space as
        # Active Flight Plan / Airport Info. Keep underlying state,
        # suppress this old presentation.
        return

        # GLASS_PANEL_NO_BRUSH
        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        if not hasattr(self, "aircraft"):
            return

        engine_state = getattr(
            self.aircraft,
            "engine_state",
            None,
        )

        if engine_state is None:
            return

        engine_health = engine_state.health

        engine = engine_state.data
        engine_health = engine_state.health
        engine_analysis = engine_state.analysis
        engine_trend = engine_state.trend

        flight_state = self.aircraft.flight_state

        phase = flight_state.phase
        moving = "MOVING" if flight_state.aircraft_moving else "STOPPED"
        airborne = "AIRBORNE" if flight_state.airborne else "GROUND"

        box_w = 172
        box_h = 145
        box_x = 842
        box_y = 45

        painter.setPen(QPen(QColor(0, 180, 255), 2))
        painter.drawRect(box_x, box_y, box_w, box_h)

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
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
            f"CKLST {checklist_mode}",
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
            f"ENG {engine_score}% {engine_status}",
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
            f"AI {title[:10]} {severity}",
        )

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            box_x + 10,
            box_y + 144,
            action[:18],
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

    def draw_direct_to_guidance_box(
            self,
            painter: QPainter,
            width: int,
            height: int,
        ) -> None:
            # GLASS_PANEL_NO_BRUSH
            painter.setBrush(
                QBrush(
                    Qt.BrushStyle.NoBrush
                )
            )

            state = self.direct_to_guidance_state

            if not state.active:
                return

            watchdog = self.sensor_watchdog_state
            position_usable = bool(
                self.pfd is not None
                and self.pfd.position_valid
                and watchdog.position_valid
                and watchdog.position_fresh
            )

            box_w = 300
            box_h = 95
            box_x = width // 2 - box_w // 2
            box_y = 245


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
                    (
                        f"BRG {bearing:.0f}°   "
                        f"DIS {distance:.1f} NM"
                    )
                    if position_usable
                    else "BRG ---   DIS ---"
                ),
            )

            if not position_usable:
                correction_text = "COURSE ---"
            elif abs(error) < 1.0:
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
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Blake PFD visual demo"
    )

    mode_group = (
        parser.add_mutually_exclusive_group()
    )

    mode_group.add_argument(
        "--sim",
        action="store_true",
        help="Run using simulated sensor data",
    )

    mode_group.add_argument(
        "--hardware",
        action="store_true",
        help="Run using real hardware sensor readers",
    )

    mode_group.add_argument(
        "--replay-log",
        help="Replay a recorded flight log CSV",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    app = QApplication(sys.argv)

    window = BlakePfdDemo(
        use_hardware=args.hardware,
        replay_log=args.replay_log,
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
