from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class SafeTaxiGroundState:
    confirmed: bool = False
    airborne_seen: bool = False


class SafeTaxiGroundGate:
    """
    Stateful, fail-closed confirmation that the aircraft is
    genuinely in a ground-like condition before Safe Taxi may
    replace the primary flight display.

    Two confirmation paths exist:

    1. Stationary startup:
       Very low IAS/GS and low vertical speed must persist for
       a sustained dwell.

    2. Post-flight landing:
       Airborne operation must have previously been observed,
       followed by a landing-roll indication plus low IAS/GS
       and low vertical speed for a sustained dwell.

    A single low-speed frame can never confirm ground status.
    """

    def __init__(
        self,
        *,
        stationary_confirm_seconds: float = 8.0,
        landing_confirm_seconds: float = 3.0,
        stationary_max_groundspeed_kt: float = 2.0,
        stationary_max_ias_kt: float = 5.0,
        landing_max_groundspeed_kt: float = 25.0,
        landing_max_ias_kt: float = 40.0,
        max_abs_vsi_fpm: float = 100.0,
        confirmed_exit_groundspeed_kt: float = 35.0,
        confirmed_exit_ias_kt: float = 40.0,
    ) -> None:
        values = (
            stationary_confirm_seconds,
            landing_confirm_seconds,
            stationary_max_groundspeed_kt,
            stationary_max_ias_kt,
            landing_max_groundspeed_kt,
            landing_max_ias_kt,
            max_abs_vsi_fpm,
            confirmed_exit_groundspeed_kt,
            confirmed_exit_ias_kt,
        )

        if not all(
            isfinite(float(value))
            for value in values
        ):
            raise ValueError(
                "Safe Taxi ground-gate configuration "
                "must be finite"
            )

        if (
            stationary_confirm_seconds < 0.0
            or landing_confirm_seconds < 0.0
        ):
            raise ValueError(
                "Safe Taxi confirmation dwell "
                "must be nonnegative"
            )

        if any(
            value < 0.0
            for value in values[2:]
        ):
            raise ValueError(
                "Safe Taxi ground-gate limits "
                "must be nonnegative"
            )

        self.stationary_confirm_seconds = float(
            stationary_confirm_seconds
        )
        self.landing_confirm_seconds = float(
            landing_confirm_seconds
        )

        self.stationary_max_groundspeed_kt = float(
            stationary_max_groundspeed_kt
        )
        self.stationary_max_ias_kt = float(
            stationary_max_ias_kt
        )

        self.landing_max_groundspeed_kt = float(
            landing_max_groundspeed_kt
        )
        self.landing_max_ias_kt = float(
            landing_max_ias_kt
        )

        self.max_abs_vsi_fpm = float(
            max_abs_vsi_fpm
        )

        self.confirmed_exit_groundspeed_kt = float(
            confirmed_exit_groundspeed_kt
        )
        self.confirmed_exit_ias_kt = float(
            confirmed_exit_ias_kt
        )

        self._confirmed = False
        self._airborne_seen = False

        self._candidate_kind: str | None = None
        self._candidate_since_s: float | None = None
        self._last_now_s: float | None = None

    @staticmethod
    def _finite(value) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(result):
            return None

        return result

    def _state(self) -> SafeTaxiGroundState:
        return SafeTaxiGroundState(
            confirmed=self._confirmed,
            airborne_seen=self._airborne_seen,
        )

    def _reset_candidate(self) -> None:
        self._candidate_kind = None
        self._candidate_since_s = None

    def _fail_closed(
        self,
    ) -> SafeTaxiGroundState:
        self._confirmed = False
        self._reset_candidate()
        return self._state()

    def update(
        self,
        *,
        flight,
        flight_state,
        inputs_fresh: bool,
        now_s: float,
    ) -> SafeTaxiGroundState:
        now = self._finite(now_s)

        if now is None:
            return self._fail_closed()

        if (
            self._last_now_s is not None
            and now < self._last_now_s
        ):
            self._last_now_s = now
            return self._fail_closed()

        self._last_now_s = now

        if not inputs_fresh:
            return self._fail_closed()

        if flight is None or flight_state is None:
            return self._fail_closed()

        gs = self._finite(
            getattr(
                flight,
                "ground_speed_kt",
                None,
            )
        )

        ias = self._finite(
            getattr(
                flight,
                "ias_kt",
                None,
            )
        )

        vsi = self._finite(
            getattr(
                flight,
                "vsi_fpm",
                None,
            )
        )

        if (
            gs is None
            or ias is None
            or vsi is None
            or gs < 0.0
            or ias < 0.0
        ):
            return self._fail_closed()

        airborne = bool(
            getattr(
                flight_state,
                "airborne",
                True,
            )
        )

        landing_roll = bool(
            getattr(
                flight_state,
                "landing_roll",
                False,
            )
        )

        if airborne:
            self._airborne_seen = True
            return self._fail_closed()

        # Once ground status is confirmed, retain it during
        # ordinary taxi. Immediately remove confirmation if
        # the aircraft leaves the conservative ground envelope.
        if self._confirmed:
            if (
                gs
                <= self.confirmed_exit_groundspeed_kt
                and ias
                <= self.confirmed_exit_ias_kt
                and abs(vsi)
                <= self.max_abs_vsi_fpm
            ):
                return self._state()

            return self._fail_closed()

        stationary_candidate = (
            gs
            <= self.stationary_max_groundspeed_kt
            and ias
            <= self.stationary_max_ias_kt
            and abs(vsi)
            <= self.max_abs_vsi_fpm
        )

        landing_candidate = (
            self._airborne_seen
            and landing_roll
            and gs
            <= self.landing_max_groundspeed_kt
            and ias
            <= self.landing_max_ias_kt
            and abs(vsi)
            <= self.max_abs_vsi_fpm
        )

        if landing_candidate:
            candidate_kind = "landing"
            required_dwell = (
                self.landing_confirm_seconds
            )
        elif stationary_candidate:
            candidate_kind = "stationary"
            required_dwell = (
                self.stationary_confirm_seconds
            )
        else:
            self._reset_candidate()
            return self._state()

        if self._candidate_kind != candidate_kind:
            self._candidate_kind = candidate_kind
            self._candidate_since_s = now
            return self._state()

        if self._candidate_since_s is None:
            self._candidate_since_s = now
            return self._state()

        elapsed = now - self._candidate_since_s

        if elapsed >= required_dwell:
            self._confirmed = True
            self._reset_candidate()

        return self._state()
