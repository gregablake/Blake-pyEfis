from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set fuel totalizer values")
    parser.add_argument("--total-gal", type=float, default=24.0)
    parser.add_argument("--remaining-gal", type=float)

    args = parser.parse_args()

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    raw.setdefault("fuel", {})

    raw["fuel"]["total_gal"] = args.total_gal
    raw["fuel"]["remaining_gal"] = (
        args.remaining_gal if args.remaining_gal is not None else args.total_gal
    )

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"Fuel total: {raw['fuel']['total_gal']:.1f} gal")
    print(f"Fuel remaining: {raw['fuel']['remaining_gal']:.1f} gal")


if __name__ == "__main__":
    main()