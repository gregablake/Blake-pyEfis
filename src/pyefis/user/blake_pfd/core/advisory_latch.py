from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdvisoryLatchState:
    active_key: str | None = None
    active_severity: str = "NORMAL"

    pending_key: str | None = None
    pending_severity: str = "NORMAL"

    consecutive_active_samples: int = 0
    consecutive_pending_samples: int = 0
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

        self.state.consecutive_clear_samples = 0

        # A more severe condition replaces the current advisory immediately.
        if (
            self.state.active_key is not None
            and new_rank > current_rank
        ):
            self._activate(
                key=key,
                severity=severity,
            )
            return self.state

        # No advisory is active yet. Require repeated matching samples.
        if self.state.active_key is None:
            if key != self.state.pending_key:
                self._start_pending(
                    key=key,
                    severity=severity,
                )
            else:
                self.state.consecutive_pending_samples += 1

            if (
                self.state.consecutive_pending_samples
                >= self.activate_samples
            ):
                self._activate(
                    key=key,
                    severity=severity,
                )

            return self.state

        # The current advisory remains present.
        if (
            key == self.state.active_key
            and severity == self.state.active_severity
        ):
            self.state.consecutive_active_samples += 1
            self._clear_pending()
            return self.state

        # A different advisory must persist before replacing the current one.
        if (
            key != self.state.pending_key
            or severity != self.state.pending_severity
        ):
            self._start_pending(
                key=key,
                severity=severity,
            )
        else:
            self.state.consecutive_pending_samples += 1

        if (
            self.state.consecutive_pending_samples
            >= self.activate_samples
        ):
            self._activate(
                key=key,
                severity=severity,
            )

        return self.state

    def _handle_clear(self) -> AdvisoryLatchState:
        self.state.consecutive_active_samples = 0
        self._clear_pending()

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

    def _activate(
        self,
        key: str,
        severity: str,
    ) -> None:
        self.state.active_key = key
        self.state.active_severity = severity
        self.state.consecutive_active_samples = (
            self.activate_samples
        )
        self.state.consecutive_clear_samples = 0
        self._clear_pending()

    def _start_pending(
        self,
        key: str,
        severity: str,
    ) -> None:
        self.state.pending_key = key
        self.state.pending_severity = severity
        self.state.consecutive_pending_samples = 1

    def _clear_pending(self) -> None:
        self.state.pending_key = None
        self.state.pending_severity = "NORMAL"
        self.state.consecutive_pending_samples = 0