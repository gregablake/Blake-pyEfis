from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnginePrediction:
    cht_limit_f: float = 430.0
    oil_temp_limit_f: float = 250.0

    time_to_cht_limit_s: float | None = None
    time_to_oil_temp_limit_s: float | None = None

    message: str = "No predicted exceedance."
    severity: str = "NORMAL"


class EnginePredictor:
    def predict(self, trend) -> EnginePrediction:
        sample_count = getattr(trend, "sample_count", 0)

        if sample_count < 5:
            return EnginePrediction(
                message="Collecting trend data.",
                severity="NORMAL",
            )

        history_duration_s = getattr(
            trend,
            "history_duration_s",
            0.0,
        )

        if history_duration_s < 2.0:
            return EnginePrediction(
                message="Collecting trend history.",
                severity="NORMAL",
            )

        cht_rate = max(getattr(trend, "cht_rate", 0.0), 0.0)
        oil_rate = max(getattr(trend, "oil_temp_rate", 0.0), 0.0)

        current_cht = getattr(trend, "current_cht", 0.0)
        current_oil = getattr(trend, "current_oil_temp", 0.0)
        
        sample_count = getattr(trend, "sample_count", 0)

        if sample_count < 5:
            return EnginePrediction(
            message="Collecting trend data.",
            severity="NORMAL",
            )

        prediction = EnginePrediction()

        if cht_rate > 0:
            delta = prediction.cht_limit_f - current_cht

            if delta > 0:
                prediction.time_to_cht_limit_s = delta / cht_rate

        if oil_rate > 0:
            delta = prediction.oil_temp_limit_f - current_oil

            if delta > 0:
                prediction.time_to_oil_temp_limit_s = delta / oil_rate

        if (
            prediction.time_to_cht_limit_s is not None
            and prediction.time_to_cht_limit_s < 60
        ):
            prediction.severity = "CAUTION"
            prediction.message = (
                f"CHT predicted to reach limit in "
                f"{prediction.time_to_cht_limit_s:.0f}s."
            )

        if (
            prediction.time_to_oil_temp_limit_s is not None
            and prediction.time_to_oil_temp_limit_s < 60
        ):
            prediction.severity = "CAUTION"
            prediction.message = (
                f"Oil temperature predicted to reach limit in "
                f"{prediction.time_to_oil_temp_limit_s:.0f}s."
            )

        return prediction