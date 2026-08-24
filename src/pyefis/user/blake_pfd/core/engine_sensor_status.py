from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EngineChannelStatus:
    valid: bool = False
    fresh: bool = False
    message: str = "NO DATA"


@dataclass(frozen=True)
class EngineSensorStatus:
    rpm: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    volts: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    amps: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    oil_pressure: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    oil_temperature: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    fuel_pressure: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    fuel_flow: EngineChannelStatus = field(
        default_factory=EngineChannelStatus
    )

    cht: tuple[EngineChannelStatus, ...] = field(
        default_factory=lambda: tuple(
            EngineChannelStatus()
            for _ in range(6)
        )
    )

    egt: tuple[EngineChannelStatus, ...] = field(
        default_factory=lambda: tuple(
            EngineChannelStatus()
            for _ in range(2)
        )
    )