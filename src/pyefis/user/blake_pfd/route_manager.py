from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from pyefis.user.blake_pfd.database_importer import AviationDatabase
from pyefis.user.blake_pfd.nav_math import bearing_between_points_deg


ROUTE_PATH = Path(__file__).with_name("active_route.yaml")


@dataclass
class RouteLeg:
    from_ident: str
    to_ident: str
    desired_track_deg: float


class RouteManager:
    def __init__(self) -> None:
        self.database = AviationDatabase()
        self.database.load_all()

    def create_direct_route(
        self,
        from_ident: str,
        to_ident: str,
    ) -> RouteLeg:
        from_airport = self.database.get_airport(from_ident)
        to_airport = self.database.get_airport(to_ident)

        if from_airport is None:
            raise ValueError(f"From airport not found: {from_ident}")

        if to_airport is None:
            raise ValueError(f"To airport not found: {to_ident}")

        desired_track = bearing_between_points_deg(
            from_airport.lat_deg,
            from_airport.lon_deg,
            to_airport.lat_deg,
            to_airport.lon_deg,
        )

        return RouteLeg(
            from_ident=from_airport.ident,
            to_ident=to_airport.ident,
            desired_track_deg=desired_track,
        )

    def save_route(self, route_id: str, waypoints: list[str]) -> None:
        raw = {
            "route_id": route_id,
            "waypoints": [wp.upper() for wp in waypoints],
            "active_leg_index": 0,
        }

        ROUTE_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    def load_route(self) -> dict:
        if not ROUTE_PATH.exists():
            return {
                "route_id": "",
                "waypoints": [],
                "active_leg_index": 0,
            }

        return yaml.safe_load(ROUTE_PATH.read_text()) or {}

    def get_active_leg(self) -> RouteLeg | None:
        route = self.load_route()
        waypoints = route.get("waypoints", [])
        active_leg_index = int(route.get("active_leg_index", 0))

        if len(waypoints) < 2:
            return None

        if active_leg_index >= len(waypoints) - 1:
            return None

        return self.create_direct_route(
            waypoints[active_leg_index],
            waypoints[active_leg_index + 1],
        )
        
    def advance_leg(self) -> bool:
        route = self.load_route()
        waypoints = route.get("waypoints", [])
        active_leg_index = int(route.get("active_leg_index", 0))

        if len(waypoints) < 2:
            return False

        if active_leg_index >= len(waypoints) - 2:
            return False

        route["active_leg_index"] = active_leg_index + 1
        ROUTE_PATH.write_text(yaml.safe_dump(route, sort_keys=False))

        return True
    def maybe_advance_leg(self, distance_to_waypoint_nm: float, sequence_distance_nm: float) -> bool:
        if distance_to_waypoint_nm > sequence_distance_nm:
            return False

        return self.advance_leg()

def demo() -> None:
    manager = RouteManager()

    manager.save_route(
        route_id="TEST_ROUTE",
        waypoints=["KLUK", "KHAO", "KCVG"],
    )

    route = manager.load_route()
    leg = manager.get_active_leg()

    print("===== Route Manager Demo =====")
    print(route)
    print(leg)


if __name__ == "__main__":
    demo()