from __future__ import annotations

from pyefis.user.blake_pfd.core.advisory_latch import (
    AdvisoryLatch,
)


class RecommendationDisplayStabilizer:
    def __init__(
        self,
        activate_samples: int = 3,
        clear_samples: int = 5,
    ) -> None:
        self._latch = AdvisoryLatch(
            activate_samples=activate_samples,
            clear_samples=clear_samples,
        )

        self._active_recommendation = None

    def update(self, recommendation):
        severity = str(
            getattr(
                recommendation,
                "severity",
                "NORMAL",
            )
        ).upper()

        # Never delay or latch an actual warning or critical condition.
        if severity in {"WARNING", "CRITICAL"}:
            self.reset()
            return recommendation

        if severity == "CAUTION":
            title = str(
                getattr(
                    recommendation,
                    "title",
                    "Engine Caution",
                )
            )

            state = self._latch.update(
                key=title,
                severity=severity,
            )

            if state.active_key is None:
                return None

            if state.active_key == title:
                self._active_recommendation = recommendation

            return self._active_recommendation

        state = self._latch.update(
            key=None,
            severity="NORMAL",
        )

        if state.active_key is None:
            self._active_recommendation = None

        return self._active_recommendation

    def reset(self) -> None:
        self._latch = AdvisoryLatch(
            activate_samples=self._latch.activate_samples,
            clear_samples=self._latch.clear_samples,
        )

        self._active_recommendation = None