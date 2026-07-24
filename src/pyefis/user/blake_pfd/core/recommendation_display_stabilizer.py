from dataclasses import dataclass
from time import monotonic

@dataclass(frozen=True)
class RecommendationDisplayStatus:
    state: str = "IDLE"
    active_title: str | None = None
    pending_title: str | None = None
    seconds_remaining: float | None = None
class RecommendationDisplayStabilizer:
    def __init__(
        self,
        activate_delay_s: float = 1.5,
        clear_delay_s: float = 2.5,
    ) -> None:
        if activate_delay_s < 0.0:
            raise ValueError(
                "activate_delay_s must not be negative"
            )

        if clear_delay_s < 0.0:
            raise ValueError(
                "clear_delay_s must not be negative"
            )

        self.activate_delay_s = float(
            activate_delay_s
        )

        self.clear_delay_s = float(
            clear_delay_s
        )

        self._active_recommendation = None
        self._pending_recommendation = None
        self._pending_key: str | None = None
        self._pending_since_s: float | None = None
        self._clear_since_s: float | None = None

    def update(
        self,
        recommendation,
        timestamp_s: float | None = None,
    ):
        now_s = (
            monotonic()
            if timestamp_s is None
            else float(timestamp_s)
        )

        severity = str(
            getattr(
                recommendation,
                "severity",
                "NORMAL",
            )
        ).upper()

        if severity in {"WARNING", "CRITICAL"}:
            self.reset()
            return recommendation

        if severity == "CAUTION":
            self._clear_since_s = None

            key = self._recommendation_key(
                recommendation
            )

            if self._active_key() == key:
                self._active_recommendation = recommendation
                self._clear_pending()
                return self._active_recommendation

            if self._pending_key != key:
                self._pending_key = key
                self._pending_recommendation = recommendation
                self._pending_since_s = now_s

                if self.activate_delay_s == 0.0:
                    return self._activate_pending()

                return self._active_recommendation

            self._pending_recommendation = recommendation

            elapsed_s = (
                now_s - self._pending_since_s
                if self._pending_since_s is not None
                else 0.0
            )

            if elapsed_s >= self.activate_delay_s:
                return self._activate_pending()

            return self._active_recommendation

        self._clear_pending()

        if self._active_recommendation is None:
            self._clear_since_s = None
            return None

        if self._clear_since_s is None:
            self._clear_since_s = now_s

            if self.clear_delay_s == 0.0:
                self._active_recommendation = None

            return self._active_recommendation

        elapsed_s = now_s - self._clear_since_s

        if elapsed_s >= self.clear_delay_s:
            self._active_recommendation = None
            self._clear_since_s = None

        return self._active_recommendation
    
    def status(
        self,
        timestamp_s: float | None = None,
    ) -> RecommendationDisplayStatus:
        now_s = (
            monotonic()
            if timestamp_s is None
            else float(timestamp_s)
        )

        if self._pending_recommendation is not None:
            elapsed_s = (
                now_s - self._pending_since_s
                if self._pending_since_s is not None
                else 0.0
            )

            seconds_remaining = max(
                0.0,
                self.activate_delay_s - elapsed_s,
            )

            return RecommendationDisplayStatus(
                state="PENDING",
                active_title=self._title(
                    self._active_recommendation
                ),
                pending_title=self._title(
                    self._pending_recommendation
                ),
                seconds_remaining=seconds_remaining,
            )

        if self._active_recommendation is not None:
            if self._clear_since_s is not None:
                elapsed_s = now_s - self._clear_since_s

                seconds_remaining = max(
                    0.0,
                    self.clear_delay_s - elapsed_s,
                )

                return RecommendationDisplayStatus(
                    state="CLEARING",
                    active_title=self._title(
                        self._active_recommendation
                    ),
                    seconds_remaining=seconds_remaining,
                )

            return RecommendationDisplayStatus(
                state="ACTIVE",
                active_title=self._title(
                    self._active_recommendation
                ),
            )

        return RecommendationDisplayStatus()

    def reset(self) -> None:
        self._active_recommendation = None
        self._pending_recommendation = None
        self._pending_key = None
        self._pending_since_s = None
        self._clear_since_s = None

    def _activate_pending(self):
        self._active_recommendation = (
            self._pending_recommendation
        )

        self._clear_pending()
        return self._active_recommendation

    def _clear_pending(self) -> None:
        self._pending_recommendation = None
        self._pending_key = None
        self._pending_since_s = None

    def _active_key(self) -> str | None:
        if self._active_recommendation is None:
            return None

        return self._recommendation_key(
            self._active_recommendation
        )
        
    @staticmethod
    def _title(
        recommendation,
    ) -> str | None:
        if recommendation is None:
            return None

        return str(
            getattr(
                recommendation,
                "title",
                "Engine Caution",
            )
        ).strip()

    @classmethod
    def _recommendation_key(
        cls,
        recommendation,
    ) -> str:
        return (
            cls._title(recommendation)
            or "ENGINE CAUTION"
        ).upper()