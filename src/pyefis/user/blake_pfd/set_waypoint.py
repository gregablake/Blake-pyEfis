from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from pyefis.user.blake_pfd.database_importer import AviationDatabase


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def set_waypoint(ident: str) -> None:
    ident = ident.upper()

    db = AviationDatabase()
    db.load_all()

    airport = db.get_airport(ident)

    if airport is None:
        raise SystemExit(f"Airport/navpoint not found: {ident}")

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("navigation", {})
    raw["navigation"]["selected_waypoint_id"] = airport.ident
    raw["navigation"]["selected_waypoint_name"] = airport.name
    raw["navigation"]["selected_waypoint_lat"] = airport.lat_deg
    raw["navigation"]["selected_waypoint_lon"] = airport.lon_deg
    raw["navigation"]["desired_track_deg"] = 0.0

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"Selected waypoint set to {airport.ident} - {airport.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set Blake PFD selected waypoint")
    parser.add_argument("ident", help="Airport/navpoint ident, example: KHAO")

    args = parser.parse_args()
    set_waypoint(args.ident)


if __name__ == "__main__":
    main()