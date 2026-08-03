from __future__ import annotations

from dataclasses import dataclass

from pyefis.user.blake_pfd.core.terrain_awareness import (
    TerrainAwareness,
    TerrainAwarenessState,
)
from pyefis.user.blake_pfd.core.terrain_profile_provider import (
    TerrainProfile,
    TerrainProfileProvider,
)


@dataclass(frozen=True)
class TerrainAwarenessManagerState:
    profile: TerrainProfile = TerrainProfile()
    awareness: TerrainAwarenessState = (
        TerrainAwarenessState()
    )
    valid: bool = False
    message: str = ""


class TerrainAwarenessManager:
    def __init__(
        self,
        *,
        profile_provider: TerrainProfileProvider,
        awareness: TerrainAwareness | None = None,
    ) -> None:
        self.profile_provider = profile_provider

        self.awareness = (
            awareness
            if awareness is not None
            else TerrainAwareness()
        )

        self.state = TerrainAwarenessManagerState()

    def update(
        self,
        *,
        aircraft_lat_deg,
        aircraft_lon_deg,
        course_deg,
        aircraft_altitude_ft,
        vertical_speed_fpm=0.0,
        ground_speed_kt=0.0,
        position_valid: bool = True,
    ) -> TerrainAwarenessManagerState:
        if not position_valid:
            self.state = TerrainAwarenessManagerState(
                message="AIRCRAFT POSITION INVALID",
            )
            return self.state

        profile = self.profile_provider.build_profile(
            aircraft_lat_deg=aircraft_lat_deg,
            aircraft_lon_deg=aircraft_lon_deg,
            course_deg=course_deg,
        )

        if not profile.valid:
            self.state = TerrainAwarenessManagerState(
                profile=profile,
                message=profile.message,
            )
            return self.state

        awareness_state = self.awareness.evaluate(
            aircraft_altitude_ft=(
                aircraft_altitude_ft
            ),
            vertical_speed_fpm=(
                vertical_speed_fpm
            ),
            ground_speed_kt=ground_speed_kt,
            profile=profile.points,
        )

        if not awareness_state.valid:
            self.state = TerrainAwarenessManagerState(
                profile=profile,
                awareness=awareness_state,
                message=awareness_state.message,
            )
            return self.state

        self.state = TerrainAwarenessManagerState(
            profile=profile,
            awareness=awareness_state,
            valid=True,
            message=awareness_state.message,
        )

        return self.state

    def clear(self) -> None:
        self.state = TerrainAwarenessManagerState()