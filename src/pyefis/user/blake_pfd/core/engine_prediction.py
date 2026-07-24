from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnginePrediction:
    cht_limit_f: float = 430.0
    oil_temp_limit_f: float = 250.0

    time_to_cht_limit_s: float | None = None
    time_to_oil_temp_limit_s: float | None = None

    cht_rate_f_per_s: float = 0.0
    oil_temp_rate_f_per_s: float = 0.0

    message: str = "No predicted exceedance."
    severity: str = "NORMAL"
    confidence: float = 0.0


class EnginePredictor:
    def __init__(
        self,
        minimum_confidence: float = 0.10,
    ) -> None:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0 and 1"
            )

        self.minimum_confidence = float(
            minimum_confidence
        )

    def predict(self, trend) -> EnginePrediction:
        sample_count = getattr(
            trend,
            "sample_count",
            0,
        )

        if sample_count < 5:
            return EnginePrediction(
                message="Collecting trend data.",
                severity="NORMAL",
                confidence=0.0,
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
                confidence=0.0,
            )

        confidence = min(
            1.0,
            sample_count / 20.0,
        )

        confidence *= min(
            1.0,
            history_duration_s / 10.0,
        )

        cht_rate = max(
            float(
                getattr(
                    trend,
                    "cht_rate",
                    0.0,
                )
            ),
            0.0,
        )

        oil_rate = max(
            float(
                getattr(
                    trend,
                    "oil_temp_rate",
                    0.0,
                )
            ),
            0.0,
        )

        current_cht = float(
            getattr(
                trend,
                "current_cht",
                0.0,
            )
        )

        current_oil = float(
            getattr(
                trend,
                "current_oil_temp",
                0.0,
            )
        )

        prediction = EnginePrediction(
            confidence=confidence,
            cht_rate_f_per_s=cht_rate,
            oil_temp_rate_f_per_s=oil_rate,
        )

        if cht_rate > 0.0:
            cht_delta = (
                prediction.cht_limit_f
                - current_cht
            )

            if cht_delta <= 0.0:
                prediction.time_to_cht_limit_s = 0.0
            else:
                prediction.time_to_cht_limit_s = (
                    cht_delta / cht_rate
                )

        if oil_rate > 0.0:
            oil_delta = (
                prediction.oil_temp_limit_f
                - current_oil
            )

            if oil_delta <= 0.0:
                prediction.time_to_oil_temp_limit_s = 0.0
            else:
                prediction.time_to_oil_temp_limit_s = (
                    oil_delta / oil_rate
                )

        urgent_predictions = [
            (
                "CHT",
                prediction.time_to_cht_limit_s,
                cht_rate,
            ),
            (
                "Oil temperature",
                prediction.time_to_oil_temp_limit_s,
                oil_rate,
            ),
        ]

        urgent_predictions = [
            item
            for item in urgent_predictions
            if (
                item[1] is not None
                and item[1] < 60.0
            )
        ]

        if not urgent_predictions:
            return prediction
        
        if confidence < self.minimum_confidence:
            prediction.message = (
                "Potential limit trend detected; "
                "collecting prediction confidence."
            )
            return prediction

        name, time_to_limit_s, rate = min(
            urgent_predictions,
            key=lambda item: item[1],
        )

        prediction.severity = "CAUTION"
        prediction.message = (
            f"{name} rising at "
            f"{rate:.1f}F/s; predicted to reach "
            f"limit in {time_to_limit_s:.0f}s."
        )

        return prediction