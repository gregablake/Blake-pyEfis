from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def set_obs(enabled: bool, selected_course_deg: float) -> None:
    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("obs", {})
    raw["obs"]["enabled"] = enabled
    raw["obs"]["selected_course_deg"] = selected_course_deg % 360.0

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print()
    print(f"OBS enabled: {enabled}")
    print(f"Selected course: {selected_course_deg % 360.0:.0f}°")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Set OBS mode")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--course", type=float, default=0.0)

    args = parser.parse_args()

    enabled = args.enable and not args.disable
    set_obs(enabled=enabled, selected_course_deg=args.course)


if __name__ == "__main__":
    main()