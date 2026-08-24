from __future__ import annotations

import math

from pyefis.user.blake_pfd.core.engine_sensor_status import (
    EngineChannelStatus,
    EngineSensorStatus,
)
from pyefis.user.blake_pfd.engine_data import EngineData


class EngineSensorMonitor:
    def evaluate(
        self,
        engine: EngineData,
        *,
        source_fresh: bool,
    ) -> EngineSensorStatus:
        def scalar_status(
            value: float,
            *,
            minimum: float | None = None,
            maximum: float | None = None,
        ) -> EngineChannelStatus:
            numeric_value = float(value)

            if not math.isfinite(numeric_value):
                return EngineChannelStatus(
                    valid=False,
                    fresh=False,
                    message="INVALID DATA",
                )

            if (
                minimum is not None
                and numeric_value < minimum
            ):
                return EngineChannelStatus(
                    valid=False,
                    fresh=False,
                    message="IMPLAUSIBLE DATA",
                )

            if (
                maximum is not None
                and numeric_value > maximum
            ):
                return EngineChannelStatus(
                    valid=False,
                    fresh=False,
                    message="IMPLAUSIBLE DATA",
                )

            if not source_fresh:
                return EngineChannelStatus(
                    valid=True,
                    fresh=False,
                    message="DATA STALE",
                )

            return EngineChannelStatus(
                valid=True,
                fresh=True,
                message="DATA VALID",
            )

        return EngineSensorStatus(
            rpm=scalar_status(
                engine.rpm,
                minimum=0.0,
                maximum=5000.0,
            ),
            volts=scalar_status(
                engine.volts,
                minimum=0.0,
                maximum=20.0,
            ),
            amps=scalar_status(
                engine.amps,
                minimum=-100.0,
                maximum=100.0,
            ),
            oil_pressure=scalar_status(
                engine.oil_pressure_psi,
                minimum=0.0,
                maximum=150.0,
            ),
            oil_temperature=scalar_status(
                engine.oil_temp_f,
                minimum=-100.0,
                maximum=350.0,
            ),
            fuel_pressure=scalar_status(
                engine.fuel_pressure_psi,
                minimum=0.0,
                maximum=30.0,
            ),
            fuel_flow=scalar_status(
                engine.fuel_flow_gph,
                minimum=0.0,
                maximum=50.0,
            ),
            
            cht=tuple(
                scalar_status(
                    value,
                    minimum=-100.0,
                    maximum=600.0,
                )
                for value in engine.cht_f
            ),
            egt=tuple(
                scalar_status(
                    value,
                    minimum=-100.0,
                    maximum=2200.0,
                )
                for value in engine.egt_f
            ),
        )
        
    def test_engine_sensor_monitor_rejects_implausible_rpm() -> None:
        monitor = EngineSensorMonitor()

        result = monitor.evaluate(
            EngineData(
                rpm=9000.0,
            ),
            source_fresh=True,
        )

        assert result.rpm.valid is False
        assert result.rpm.fresh is False
        assert result.rpm.message == "IMPLAUSIBLE DATA"


    def test_engine_sensor_monitor_rejects_implausible_oil_pressure() -> None:
        monitor = EngineSensorMonitor()

        result = monitor.evaluate(
            EngineData(
                oil_pressure_psi=-5.0,
            ),
            source_fresh=True,
        )

        assert result.oil_pressure.valid is False
        assert result.oil_pressure.fresh is False
        assert (
            result.oil_pressure.message
            == "IMPLAUSIBLE DATA"
        )
            