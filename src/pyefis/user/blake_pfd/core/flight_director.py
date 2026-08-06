from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class FlightDirectorState:
    valid: bool = False
    active: bool = False
    roll_command_deg: float = 0.0
    pitch_command_deg: float = 0.0
    lateral_error: float = 0.0
    vertical_error: float = 0.0


class FlightDirector:
    def __init__(
        self,
        *,
        maximum_roll_command_deg: float = 20.0,
        maximum_pitch_command_deg: float = 10.0,
        lateral_gain: float = 18.0,
        vertical_gain: float = 8.0,
        command_deadband: float = 0.02,
    ) -> None:
        self.maximum_roll_command_deg = (
            self._require_positive(
                maximum_roll_command_deg,
                "maximum_roll_command_deg",
            )
        )

        self.maximum_pitch_command_deg = (
            self._require_positive(
                maximum_pitch_command_deg,
                "maximum_pitch_command_deg",
            )
        )

        self.lateral_gain = self._require_positive(
            lateral_gain,
            "lateral_gain",
        )

        self.vertical_gain = self._require_positive(
            vertical_gain,
            "vertical_gain",
        )

        self.command_deadband = (
            self._require_nonnegative(
                command_deadband,
                "command_deadband",
            )
        )

    def calculate(
        self,
        *,
        cdi,
        vdi,
        navigation_valid: bool = True,
        enabled: bool = True,
    ) -> FlightDirectorState:
        if not enabled or not navigation_valid:
            return FlightDirectorState()

        lateral_error = self._safe_clamped(
            cdi,
            -1.0,
            1.0,
        )

        vertical_error = self._safe_clamped(
            vdi,
            -1.0,
            1.0,
        )

        if (
            lateral_error is None
            or vertical_error is None
        ):
            return FlightDirectorState()

        roll_command_deg = (
            -lateral_error
            * self.lateral_gain
        )

        pitch_command_deg = (
            -vertical_error
            * self.vertical_gain
        )

        roll_command_deg = self._clamp(
            roll_command_deg,
            -self.maximum_roll_command_deg,
            self.maximum_roll_command_deg,
        )

        pitch_command_deg = self._clamp(
            pitch_command_deg,
            -self.maximum_pitch_command_deg,
            self.maximum_pitch_command_deg,
        )

        if (
            abs(
                roll_command_deg
            )
            < self.command_deadband
        ):
            roll_command_deg = 0.0

        if (
            abs(
                pitch_command_deg
            )
            < self.command_deadband
        ):
            pitch_command_deg = 0.0

        return FlightDirectorState(
            valid=True,
            active=True,
            roll_command_deg=roll_command_deg,
            pitch_command_deg=pitch_command_deg,
            lateral_error=lateral_error,
            vertical_error=vertical_error,
        )

    @staticmethod
    def _clamp(
        value: float,
        low: float,
        high: float,
    ) -> float:
        return max(
            low,
            min(
                high,
                value,
            ),
        )

    @staticmethod
    def _safe_number(
        value,
    ) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        return number

    @classmethod
    def _safe_clamped(
        cls,
        value,
        low: float,
        high: float,
    ) -> float | None:
        number = cls._safe_number(
            value
        )

        if number is None:
            return None

        return cls._clamp(
            number,
            low,
            high,
        )

    @classmethod
    def _require_positive(
        cls,
        value,
        name: str,
    ) -> float:
        number = cls._safe_number(
            value
        )

        if number is None or number <= 0.0:
            raise ValueError(
                f"{name} must be finite and positive"
            )

        return number

    @classmethod
    def _require_nonnegative(
        cls,
        value,
        name: str,
    ) -> float:
        number = cls._safe_number(
            value
        )

        if number is None or number < 0.0:
            raise ValueError(
                f"{name} must be finite and nonnegative"
            )

        return number