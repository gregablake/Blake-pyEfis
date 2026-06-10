from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


@dataclass
class WeatherMetar:
    airport_id: str
    age_min: float = 0.0
    flight_category: str = "UNK"
    wind_text: str = ""
    altimeter_inhg: float = 29.92
    raw_text: str = ""


@dataclass
class WeatherState:
    ok: bool = False
    metars: list[WeatherMetar] | None = None
    last_update_s: float = 0.0


class WeatherReader:
    """
    ADS-B weather foundation.

    Later this will parse FIS-B weather from Stratux/GDL90.
    This placeholder gives the PFD a weather data structure.
    """

    def __init__(self) -> None:
        self.ok = False
        self.last_update_s = monotonic()
        self.metars: list[WeatherMetar] = []

    def read(self) -> WeatherState:
        return WeatherState(
            ok=self.ok,
            metars=self.metars,
            last_update_s=self.last_update_s,
        )


def demo() -> None:
    reader = WeatherReader()
    print("===== Weather Reader Demo =====")
    print(reader.read())


if __name__ == "__main__":
    demo()