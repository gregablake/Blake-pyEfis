from __future__ import annotations

import argparse
import csv
from pathlib import Path


LOG_PATH = Path(__file__).parent.parent / "logs" / "efis_events.csv"


def list_events(limit: int) -> None:
    if not LOG_PATH.exists():
        print("No EFIS event log found.")
        return

    with LOG_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print()
    print("EFIS Event Log")
    print("-" * 70)

    for row in rows[-limit:]:
        print(
            f"{row.get('timestamp_utc', '')}  "
            f"{row.get('event_type', ''):<16}  "
            f"{row.get('message', '')}"
        )

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="View EFIS event log")
    parser.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()
    list_events(args.limit)


if __name__ == "__main__":
    main()
    