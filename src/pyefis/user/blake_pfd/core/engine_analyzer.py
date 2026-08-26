from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.engine_data import EngineData


@dataclass
class EngineAnalysis:
    summary: str = "Engine operating normally."
    recommendation: str = "Continue normal operation."
    severity: str = "NORMAL"
    hottest_cylinder: int = 0
    hottest_cht_f: float = 0.0
    cht_spread_f: float = 0.0
    egt_spread_f: float = 0.0


class EngineAnalyzer:
    def analyze(
        self,
        engine: EngineData,
        health=None,
        trend=None,
        sensor_status=None,
    ) -> EngineAnalysis:
        def channel_usable(status) -> bool:
            return (
                status is None
                or (
                    status.valid
                    and status.fresh
                )
            )

        cht_values_with_index = [
            (index, value)
            for index, value in enumerate(
                engine.cht_f or []
            )
            if (
                sensor_status is None
                or (
                    index < len(sensor_status.cht)
                    and channel_usable(
                        sensor_status.cht[index]
                    )
                )
            )
        ]

        egt_values = [
            value
            for index, value in enumerate(
                engine.egt_f or []
            )
            if (
                sensor_status is None
                or (
                    index < len(sensor_status.egt)
                    and channel_usable(
                        sensor_status.egt[index]
                    )
                )
            )
        ]

        if cht_values_with_index:
            hottest_index, hottest_cht = max(
                cht_values_with_index,
                key=lambda item: item[1],
            )
            hottest_cylinder = hottest_index + 1

            cht_values = [
                value
                for _, value in cht_values_with_index
            ]

            cht_spread = (
                max(cht_values)
                - min(cht_values)
            )
        else:
            hottest_cht = 0.0
            hottest_cylinder = 0
            cht_spread = 0.0

        egt_spread = (
            max(egt_values)
            - min(egt_values)
            if egt_values
            else 0.0
        )

        oil_pressure_status = (
            sensor_status.oil_pressure
            if sensor_status is not None
            else None
        )

        oil_temperature_status = (
            sensor_status.oil_temperature
            if sensor_status is not None
            else None
        )

        electrical_usable = (
            sensor_status is None
            or (
                channel_usable(sensor_status.volts)
                and channel_usable(sensor_status.amps)
            )
        )

        if (
            channel_usable(oil_pressure_status)
            and engine.oil_pressure_psi <= 15
        ):
            return EngineAnalysis(
                summary="Low oil pressure detected.",
                recommendation="Reduce power and land as soon as practical.",
                severity="CRITICAL",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if (
            channel_usable(oil_temperature_status)
            and engine.oil_temp_f >= 260
        ):
            return EngineAnalysis(
                summary="Oil temperature is above redline.",
                recommendation="Reduce power, increase airspeed, and land soon.",
                severity="CRITICAL",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if hottest_cht >= 450:
            return EngineAnalysis(
                summary=f"CHT cylinder {hottest_cylinder} is above redline.",
                recommendation="Reduce climb angle, enrich mixture, and reduce power.",
                severity="CRITICAL",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if hottest_cht >= 425:
            return EngineAnalysis(
                summary=f"CHT cylinder {hottest_cylinder} is getting hot.",
                recommendation="Increase cooling air and monitor closely.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if egt_spread >= 150:
            return EngineAnalysis(
                summary="EGT spread is elevated.",
                recommendation="Check mixture distribution and monitor cylinders.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        if (
            electrical_usable
            and not engine.alternator_online
        ):
            return EngineAnalysis(
                summary="Alternator offline.",
                recommendation="Reduce electrical load and monitor battery voltage.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )

        score = getattr(health, "health_score", 100) if health is not None else 100
        
        if trend is not None:
            trend_warning = getattr(trend, "warning", "")

            if trend_warning:
                return EngineAnalysis(
                summary=trend_warning,
                recommendation="Adjust power, airspeed, or climb rate before limits are reached.",
                severity="CAUTION",
                hottest_cylinder=hottest_cylinder,
                hottest_cht_f=hottest_cht,
                cht_spread_f=cht_spread,
                egt_spread_f=egt_spread,
            )


        return EngineAnalysis(
            summary=f"Engine operating normally. Health {score}%.",
            recommendation="Continue normal operation.",
            severity="NORMAL",
            hottest_cylinder=hottest_cylinder,
            hottest_cht_f=hottest_cht,
            cht_spread_f=cht_spread,
            egt_spread_f=egt_spread,
        )