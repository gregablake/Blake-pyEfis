from __future__ import annotations

from math import isfinite


class BaroSettingController:
    """
    Runtime pilot altimeter-setting controller.

    The setting is stored internally in hundredths of inHg
    so repeated 0.01 adjustments are deterministic and do
    not accumulate floating-point error.
    """

    MIN_INHG = 27.50
    MAX_INHG = 31.50
    STEP_INHG = 0.01

    MIN_HUNDREDTHS = 2750
    MAX_HUNDREDTHS = 3150

    def __init__(
        self,
        *,
        initial_inhg: float,
    ) -> None:
        hundredths = self._validated_hundredths(
            initial_inhg
        )

        if hundredths is None:
            raise ValueError(
                "initial BARO setting must be finite, "
                "within 27.50-31.50 inHg, and expressed "
                "to hundredths"
            )

        self._setting_hundredths = hundredths

    @property
    def setting_inhg(self) -> float:
        return (
            self._setting_hundredths
            / 100.0
        )

    def increment(self) -> float:
        self._setting_hundredths = min(
            self.MAX_HUNDREDTHS,
            self._setting_hundredths + 1,
        )

        return self.setting_inhg

    def decrement(self) -> float:
        self._setting_hundredths = max(
            self.MIN_HUNDREDTHS,
            self._setting_hundredths - 1,
        )

        return self.setting_inhg

    def set_setting(
        self,
        value_inhg,
    ) -> bool:
        hundredths = self._validated_hundredths(
            value_inhg
        )

        if hundredths is None:
            return False

        self._setting_hundredths = hundredths
        return True

    @classmethod
    def _validated_hundredths(
        cls,
        value,
    ) -> int | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        if (
            number < cls.MIN_INHG
            or number > cls.MAX_INHG
        ):
            return None

        scaled = number * 100.0
        hundredths = int(round(scaled))

        # Reject arbitrary extra precision rather than
        # silently changing a pilot/configured setting.
        if abs(
            scaled - hundredths
        ) > 1e-6:
            return None

        if not (
            cls.MIN_HUNDREDTHS
            <= hundredths
            <= cls.MAX_HUNDREDTHS
        ):
            return None

        return hundredths
