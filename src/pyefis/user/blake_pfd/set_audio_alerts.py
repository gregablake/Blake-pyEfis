from __future__ import annotations

import argparse
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).with_name("pfd_config.yaml")


def bool_from_text(value: str) -> bool:
    value = value.lower()

    if value in {"on", "true", "yes", "1", "enable", "enabled"}:
        return True

    if value in {"off", "false", "no", "0", "disable", "disabled"}:
        return False

    raise SystemExit("Use on/off, true/false, yes/no, or 1/0.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set audio alert options")
    parser.add_argument("--audio", choices=["on", "off"])
    parser.add_argument("--buzzer", choices=["on", "off"])
    parser.add_argument("--pin", type=int)
    parser.add_argument("--repeat", type=float)

    args = parser.parse_args()

    raw = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    raw.setdefault("audio_alerts", {})

    if args.audio is not None:
        raw["audio_alerts"]["enabled"] = bool_from_text(args.audio)

    if args.buzzer is not None:
        raw["audio_alerts"]["buzzer_enabled"] = bool_from_text(args.buzzer)

    if args.pin is not None:
        raw["audio_alerts"]["buzzer_pin"] = args.pin

    if args.repeat is not None:
        raw["audio_alerts"]["repeat_interval_s"] = args.repeat

    CONFIG_PATH.write_text(yaml.safe_dump(raw, sort_keys=False))

    print("Audio alert settings updated.")
    print(raw["audio_alerts"])


if __name__ == "__main__":
    main()