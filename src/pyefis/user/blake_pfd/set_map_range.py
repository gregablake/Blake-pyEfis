from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def set_map_range(range_nm: float) -> None:
    allowed = {5.0, 10.0, 25.0, 50.0, 100.0}

    if range_nm not in allowed:
        raise SystemExit("Use one of: 5, 10, 25, 50, 100")

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("moving_map", {})
    raw["moving_map"]["range_nm"] = range_nm

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"Moving map range set to {range_nm:.0f} NM")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set moving map range")
    parser.add_argument("range_nm", type=float, choices=[5, 10, 25, 50, 100])

    args = parser.parse_args()
    set_map_range(args.range_nm)


if __name__ == "__main__":
    main()