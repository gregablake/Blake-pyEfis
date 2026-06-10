from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def set_declutter(level: int) -> None:
    if level not in {0, 1, 2}:
        raise SystemExit("Declutter level must be 0, 1, or 2.")

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("declutter", {})
    raw["declutter"]["level"] = level

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"Declutter level set to {level}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set PFD declutter level")
    parser.add_argument("level", type=int, choices=[0, 1, 2])

    args = parser.parse_args()
    set_declutter(args.level)


if __name__ == "__main__":
    main()