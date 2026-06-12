from __future__ import annotations

import argparse
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=["pause", "resume", "reset"],
    )

    args = parser.parse_args()

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("simulation", {})

    if args.action == "pause":
        raw["simulation"]["paused"] = True
        print("Simulator paused")

    elif args.action == "resume":
        raw["simulation"]["paused"] = False
        print("Simulator resumed")

    elif args.action == "reset":
        raw["simulation"]["reset_counter"] = (
            raw["simulation"].get("reset_counter", 0) + 1
        )
        print("Simulator reset")

    CONFIG_PATH.write_text(
        yaml.safe_dump(raw, sort_keys=False)
    )


if __name__ == "__main__":
    main()