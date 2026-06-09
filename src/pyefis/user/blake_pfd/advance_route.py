from __future__ import annotations

from pyefis.user.blake_pfd.route_manager import RouteManager


def main() -> None:
    manager = RouteManager()

    advanced = manager.advance_leg()
    route = manager.load_route()
    active_leg = manager.get_active_leg()

    print()
    if advanced:
        print("Route advanced.")
    else:
        print("Route could not advance. Already on final leg or no route loaded.")

    print(route)
    print(active_leg)
    print()


if __name__ == "__main__":
    main()