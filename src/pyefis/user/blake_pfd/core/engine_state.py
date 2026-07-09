from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.engine_data import EngineData
from pyefis.user.blake_pfd.core.engine_manager import EngineHealth
from pyefis.user.blake_pfd.core.engine_trend_manager import EngineTrend
from pyefis.user.blake_pfd.core.engine_analyzer import EngineAnalysis
from pyefis.user.blake_pfd.core.cylinder_analyzer import CylinderAnalysis
from pyefis.user.blake_pfd.core.engine_prediction import EnginePrediction

@dataclass
class EngineState:
    data: EngineData
    health: EngineHealth
    trend: EngineTrend
    analysis: EngineAnalysis
    cylinders: CylinderAnalysis
    prediction: EnginePrediction