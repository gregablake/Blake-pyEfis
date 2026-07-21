from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdvisoryLatchState:
    active_key: str | None = None
    active_severity: str = "NORMAL"
    consecutive_active_samples: int = 0
    consecutive_clear_samples: int = 0


class AdvisoryLatch:
    _SEVERITY_ORDER = {
        "NORMAL": 0,
        "CAUTION": 1,
        "WARNING": 2,
        "CRITICAL": 3,
    }

    def __init__(
        self,
        activate_samples: int = 3,
        clear_samples: int = 5,
    ) -> None:
        if activate_samples < 1:
            raise ValueError("activate_samples must be at least 1")

        if clear_samples < 1:
            raise ValueError("clear_samples must be at least 1")

        self.activate_samples = activate_samples
        self.clear_samples = clear_samples
        self.state = AdvisoryLatchState()

    def update(
        self,
        key: str | None,
        severity: str,
    ) -> AdvisoryLatchState:
        severity = severity.upper()

        if severity not in self._SEVERITY_ORDER:
            severity = "NORMAL"

        if key is None or severity == "NORMAL":
            return self._handle_clear()

        return self._handle_active(
            key=key,
            severity=severity,
        )

    def _handle_active(
        self,
        key: str,
        severity: str,
    ) -> AdvisoryLatchState:
        current_rank = self._SEVERITY_ORDER[
            self.state.active_severity
        ]
        new_rank = self._SEVERITY_ORDER[severity]

        if (
            self.state.active_key is not None
            and new_rank > current_rank
        ):
            self.state.active_key = key
            self.state.active_severity = severity
            self.state.consecutive_active_samples = (
                self.activate_samples
            )
            self.state.consecutive_clear_samples = 0
            return self.state
        
        if self.state.active_key is None:
            self.state.consecutive_active_samples += 1
            self.state.consecutive_clear_samples = 0

            if (
                self.state.consecutive_active_samples
                >= self.activate_samples
            ):
                self.state.active_key = key
                self.state.active_severity = severity

            return self.state

        if key == self.state.active_key:
            self.state.consecutive_active_samples += 1
            self.state.consecutive_clear_samples = 0
            return self.state

        self.state.consecutive_active_samples += 1
        self.state.consecutive_clear_samples = 0

        return self.state

    def _handle_clear(self) -> AdvisoryLatchState:
        self.state.consecutive_active_samples = 0

        if self.state.active_key is None:
            self.state.consecutive_clear_samples = 0
            self.state.active_severity = "NORMAL"
            return self.state

        self.state.consecutive_clear_samples += 1

        if (
            self.state.consecutive_clear_samples
            >= self.clear_samples
        ):
            self.state = AdvisoryLatchState()

        return self.state