from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from pyefis.user.blake_pfd.database_importer import AviationDatabase
from pyefis.user.blake_pfd.nav_math import bearing_between_points_deg


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def direct_to(ident: str, from_lat: float, from_lon: float) -> None:
    ident = ident.upper()

    db = AviationDatabase()
    db.load_all()

    airport = db.get_airport(ident)

    if airport is None:
        raise SystemExit(f"Airport not found: {ident}")

    desired_track = bearing_between_points_deg(
        from_lat,
        from_lon,
        airport.lat_deg,
        airport.lon_deg,
    )

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("navigation", {})
    raw["navigation"]["selected_waypoint_id"] = airport.ident
    raw["navigation"]["selected_waypoint_name"] = airport.name
    raw["navigation"]["selected_waypoint_lat"] = airport.lat_deg
    raw["navigation"]["selected_waypoint_lon"] = airport.lon_deg
    raw["navigation"]["desired_track_deg"] = desired_track

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print()
    print(f"Direct-To set: {airport.ident} - {airport.name}")
    print(f"Desired Track: {desired_track:.1f}°")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Set Direct-To waypoint")
    parser.add_argument("ident", help="Airport ident, example: KHAO")
    parser.add_argument("--from-lat", type=float, required=True)
    parser.add_argument("--from-lon", type=float, required=True)

    args = parser.parse_args()

    direct_to(args.ident, args.from_lat, args.from_lon)


if __name__ == "__main__":
    main()