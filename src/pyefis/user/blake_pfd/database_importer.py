from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"


@dataclass
class AirportRecord:
    ident: str
    name: str
    type: str
    lat_deg: float
    lon_deg: float
    elevation_ft: float


@dataclass
class RunwayRecord:
    airport_ident: str
    length_ft: float
    width_ft: float
    surface: str
    le_ident: str
    le_heading_deg: float
    he_ident: str
    he_heading_deg: float


@dataclass
class NavaidRecord:
    ident: str
    name: str
    type: str
    lat_deg: float
    lon_deg: float
    frequency_khz: float


class AviationDatabase:
    def __init__(self) -> None:
        self.airports: dict[str, AirportRecord] = {}
        self.runways_by_airport: dict[str, list[RunwayRecord]] = {}
        self.navaids: dict[str, NavaidRecord] = {}

    def load_all(self) -> None:
        self.load_airports()
        self.load_runways()
        self.load_navaids()

    def load_airports(self) -> None:
        path = DATA_DIR / "airports.csv"

        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                ident = row["ident"].strip().upper()

                if not ident:
                    continue

                self.airports[ident] = AirportRecord(
                    ident=ident,
                    name=row["name"],
                    type=row["type"],
                    lat_deg=float(row["latitude_deg"]),
                    lon_deg=float(row["longitude_deg"]),
                    elevation_ft=float(row["elevation_ft"] or 0.0),
                )

    def load_runways(self) -> None:
        path = DATA_DIR / "runways.csv"

        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                airport_ident = row["airport_ident"].strip().upper()

                if not airport_ident:
                    continue

                runway = RunwayRecord(
                    airport_ident=airport_ident,
                    length_ft=float(row["length_ft"] or 0.0),
                    width_ft=float(row["width_ft"] or 0.0),
                    surface=row["surface"] or "",
                    le_ident=row["le_ident"] or "",
                    le_heading_deg=float(row["le_heading_degT"] or 0.0),
                    he_ident=row["he_ident"] or "",
                    he_heading_deg=float(row["he_heading_degT"] or 0.0),
                )

                self.runways_by_airport.setdefault(airport_ident, []).append(runway)

    def load_navaids(self) -> None:
        path = DATA_DIR / "navaids.csv"

        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                ident = row["ident"].strip().upper()

                if not ident:
                    continue

                self.navaids[ident] = NavaidRecord(
                    ident=ident,
                    name=row["name"],
                    type=row["type"],
                    lat_deg=float(row["latitude_deg"]),
                    lon_deg=float(row["longitude_deg"]),
                    frequency_khz=float(row["frequency_khz"] or 0.0),
                )

    def get_airport(self, ident: str) -> AirportRecord | None:
        return self.airports.get(ident.upper())

    def get_runways(self, airport_ident: str) -> list[RunwayRecord]:
        return self.runways_by_airport.get(airport_ident.upper(), [])

    def get_navaid(self, ident: str) -> NavaidRecord | None:
        return self.navaids.get(ident.upper())


def demo() -> None:
    db = AviationDatabase()
    db.load_all()

    print("===== Aviation Database Demo =====")
    print(f"Airports loaded: {len(db.airports)}")
    print(f"Navaids loaded: {len(db.navaids)}")

    for ident in ["KCVG", "KLUK", "KHAO"]:
        airport = db.get_airport(ident)
        runways = db.get_runways(ident)

        print()
        print(airport)
        print(f"Runways: {runways[:3]}")


if __name__ == "__main__":
    demo()