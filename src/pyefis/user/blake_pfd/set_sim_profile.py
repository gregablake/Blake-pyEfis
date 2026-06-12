from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


PROFILES = {
    "straight",
    "climb",
    "descent",
    "left_turn",
    "right_turn",
    "approach",
}


def set_sim_profile(profile: str) -> None:
    profile = profile.lower()

    if profile not in PROFILES:
        raise SystemExit(f"Invalid profile. Use one of: {', '.join(sorted(PROFILES))}")

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    raw.setdefault("simulation", {})
    raw["simulation"]["profile"] = profile

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print(f"Simulation profile set to: {profile}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set simulator flight profile")
    parser.add_argument("profile", choices=sorted(PROFILES))

    args = parser.parse_args()
    set_sim_profile(args.profile)


if __name__ == "__main__":
    main()