from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.config_loader import (
    BlakePfdConfig,
)
from pyefis.user.blake_pfd.core.aircraft_intelligence import (
    AircraftIntelligence,
)
from pyefis.user.blake_pfd.core.aircraft_performance_config import (
    AircraftPerformanceConfig,
)
from pyefis.user.blake_pfd.core.emergency_airport_manager import (
    EmergencyAirportManager,
)
from pyefis.user.blake_pfd.core.reachable_airport_pipeline import (
    ReachableAirportPipeline,
)


@dataclass(frozen=True)
class AircraftSystems:
    performance_config: AircraftPerformanceConfig
    aircraft_intelligence: AircraftIntelligence
    emergency_airport_manager: EmergencyAirportManager
    reachable_airport_pipeline: ReachableAirportPipeline


def build_aircraft_systems(
    config: BlakePfdConfig,
) -> AircraftSystems:
    performance_config = config.performance

    reachable_airport_pipeline = ReachableAirportPipeline(
        performance_config=performance_config,
    )

    emergency_airport_manager = EmergencyAirportManager(
        pipeline=reachable_airport_pipeline,
        performance_config=performance_config,
    )

    aircraft_intelligence = AircraftIntelligence(
        performance_config=performance_config,
    )

    return AircraftSystems(
        performance_config=performance_config,
        aircraft_intelligence=aircraft_intelligence,
        emergency_airport_manager=emergency_airport_manager,
        reachable_airport_pipeline=reachable_airport_pipeline,
    )