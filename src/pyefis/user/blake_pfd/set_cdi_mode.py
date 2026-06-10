from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def set_cdi_mode(mode: str) -> None:
    mode = mode.lower()

    allowed = {"enroute", "terminal", "approach"}

    if mode not in allowed:
        raise SystemExit(f"Invalid mode: {mode}. Use enroute, terminal, or approach.")

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("navigation_scaling", {})
    raw["navigation_scaling"]["mode"] = mode

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"CDI scaling mode set to: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set CDI scaling mode")
    parser.add_argument("mode", choices=["enroute", "terminal", "approach"])

    args = parser.parse_args()
    set_cdi_mode(args.mode)


if __name__ == "__main__":
    main()