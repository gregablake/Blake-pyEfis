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
        cht_rate = getattr(trend, "cht_rate", 0.0)
        oil_rate = getattr(trend, "oil_temp_rate", 0.0)
        predicted_cht = getattr(trend, "predicted_cht", 0.0)
        predicted_oil = getattr(trend, "predicted_oil_temp", 0.0)

        prediction = EnginePrediction()

        if predicted_cht >= prediction.cht_limit_f:
            prediction.severity = "CAUTION"
            prediction.message = "CHT projected to exceed limit soon."

        if predicted_oil >= prediction.oil_temp_limit_f:
            prediction.severity = "CAUTION"
            prediction.message = "Oil temperature projected to exceed limit soon."

        return prediction