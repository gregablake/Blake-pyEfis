from __future__ import annotations

import argparse

from pyefis.user.blake_pfd.route_manager import RouteManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Blake PFD route")
    parser.add_argument("route_id", help="Route name/id")
    parser.add_argument("waypoints", nargs="+", help="Waypoint list, example: KLUK KHAO KCVG")

    args = parser.parse_args()

    if len(args.waypoints) < 2:
        raise SystemExit("Route needs at least 2 waypoints.")

    manager = RouteManager()
    manager.save_route(args.route_id, args.waypoints)

    print()
    print(f"Route saved: {args.route_id}")
    print(" -> ".join(wp.upper() for wp in args.waypoints))
    print()


if __name__ == "__main__":
    main()