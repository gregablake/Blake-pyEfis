from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.engine_data import EngineData


@dataclass
class CylinderAnalysis:
    hottest_cylinder: int = 0
    hottest_cht_f: float = 0.0
    cht_spread_f: float = 0.0
    egt_spread_f: float = 0.0
    imbalance_detected: bool = False
    message: str = "Cylinders balanced."


class CylinderAnalyzer:
    def analyze(
        self,
        engine: EngineData,
        sensor_status=None,
    ) -> CylinderAnalysis:
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

        imbalance = cht_spread >= 60.0 or egt_spread >= 150.0

        if imbalance:
            message = (
                f"Cylinder imbalance: CHT spread {cht_spread:.0f}F, "
                f"EGT spread {egt_spread:.0f}F."
            )
        else:
            message = "Cylinders balanced."

        return CylinderAnalysis(
            hottest_cylinder=hottest_cylinder,
            hottest_cht_f=hottest_cht,
            cht_spread_f=cht_spread,
            egt_spread_f=egt_spread,
            imbalance_detected=imbalance,
            message=message,
        )