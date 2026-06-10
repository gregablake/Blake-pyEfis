from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def set_vnav(enabled: bool, glidepath_angle_deg: float) -> None:
    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("vnav", {})
    raw["vnav"]["enabled"] = enabled
    raw["vnav"]["glidepath_angle_deg"] = glidepath_angle_deg

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print()
    print(f"VNAV enabled: {enabled}")
    print(f"Glidepath angle: {glidepath_angle_deg:.1f}°")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Set VNAV/glidepath settings")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--angle", type=float, default=3.0)

    args = parser.parse_args()

    enabled = not args.disable
    if args.enable:
        enabled = True

    set_vnav(enabled=enabled, glidepath_angle_deg=args.angle)


if __name__ == "__main__":
    main()