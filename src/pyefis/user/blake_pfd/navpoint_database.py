from __future__ import annotations

from pathlib import Path

import yaml

from pyefis.user.blake_pfd.nav_math import NavPoint


NAVPOINTS_PATH = Path(__file__).with_name("navpoints.yaml")


class NavpointDatabase:
    def __init__(self, path: Path = NAVPOINTS_PATH) -> None:
        self.path = path
        self.navpoints: dict[str, NavPoint] = {}
        self.load()

    def load(self) -> None:
        raw = yaml.safe_load(self.path.read_text()) or {}
        points = raw.get("navpoints", [])

        for item in points:
            point = NavPoint(
                ident=item["ident"],
                name=item["name"],
                lat_deg=float(item["lat_deg"]),
                lon_deg=float(item["lon_deg"]),
                elevation_ft=float(item.get("elevation_ft", 0.0)),
            )
            self.navpoints[point.ident.upper()] = point

    def get(self, ident: str) -> NavPoint | None:
        return self.navpoints.get(ident.upper())

    def require(self, ident: str) -> NavPoint:
        point = self.get(ident)
        if point is None:
            raise KeyError(f"Navpoint not found: {ident}")
        return point


def demo() -> None:
    db = NavpointDatabase()

    print("===== Navpoint Database Demo =====")
    for ident, point in db.navpoints.items():
        print(ident, point)


if __name__ == "__main__":
    demo()