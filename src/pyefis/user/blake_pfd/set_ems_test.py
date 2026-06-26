from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


MODES = {
    "normal",
    "high_cht",
    "high_egt",
    "low_oil",
    "alt_fail",
    "ign_fail",
    "low_fuel",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Set EMS test mode")
    parser.add_argument("mode", choices=sorted(MODES))

    args = parser.parse_args()

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    raw.setdefault("ems_test", {})
    raw["ems_test"]["mode"] = args.mode

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"EMS test mode set to: {args.mode}")


if __name__ == "__main__":
    main()