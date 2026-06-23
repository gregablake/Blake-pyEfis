from __future__ import annotations

import argparse
import csv
from pathlib import Path


LOG_PATH = Path(__file__).parent / "logs" / "ems_alert_history.csv"


def list_alerts(limit: int) -> None:
    if not LOG_PATH.exists():
        print("No EMS alert history found.")
        return

    with LOG_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print()
    print("EMS Alert History")
    print("-" * 60)

    for row in rows[-limit:]:
        print(f"{row.get('timestamp_utc', '')}  {row.get('alert', '')}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="View EMS alert history")
    parser.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()
    list_alerts(args.limit)


if __name__ == "__main__":
    main()