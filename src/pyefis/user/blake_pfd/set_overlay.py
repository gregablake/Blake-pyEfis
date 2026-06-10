from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


OVERLAY_TO_FEATURE = {
    "map": "show_moving_map",
    "route": "show_route",
    "terrain": "show_terrain",
    "obstacles": "show_obstacles",
    "traffic": "show_traffic",
    "weather": "show_weather",
    "nearest": "show_nearest_airports",
    "airport": "show_airport_info",
    "vnav": "show_vdi",
}


def bool_from_text(value: str) -> bool:
    value = value.lower()

    if value in {"on", "true", "yes", "1", "enable", "enabled"}:
        return True

    if value in {"off", "false", "no", "0", "disable", "disabled"}:
        return False

    raise SystemExit("Use on/off, true/false, yes/no, or 1/0.")


def load_raw_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text()) or {}


def save_raw_config(raw: dict) -> None:
    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))


def set_overlay(name: str, enabled: bool) -> None:
    raw = load_raw_config()
    raw.setdefault("features", {})

    name = name.lower()

    if name == "all":
        for feature_name in OVERLAY_TO_FEATURE.values():
            raw["features"][feature_name] = enabled

        save_raw_config(raw)
        print(f"All overlay features set to: {enabled}")
        return

    if name not in OVERLAY_TO_FEATURE:
        allowed = ", ".join(sorted([*OVERLAY_TO_FEATURE.keys(), "all"]))
        raise SystemExit(f"Unknown overlay: {name}. Use one of: {allowed}")

    feature_name = OVERLAY_TO_FEATURE[name]
    raw["features"][feature_name] = enabled

    save_raw_config(raw)
    print(f"{feature_name} set to: {enabled}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set Blake PFD overlay visibility")
    parser.add_argument(
        "overlay",
        help="Overlay name: map, route, terrain, obstacles, traffic, weather, nearest, airport, vnav, all",
    )
    parser.add_argument(
        "state",
        help="on/off",
    )

    args = parser.parse_args()

    set_overlay(
        name=args.overlay,
        enabled=bool_from_text(args.state),
    )


if __name__ == "__main__":
    main()