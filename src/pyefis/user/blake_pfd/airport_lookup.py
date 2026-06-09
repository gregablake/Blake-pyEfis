from __future__ import annotations

import argparse

from pyefis.user.blake_pfd.database_importer import AviationDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Airport lookup")
    parser.add_argument("ident", help="Airport ident, example: KHAO")

    args = parser.parse_args()
    ident = args.ident.upper()

    db = AviationDatabase()
    db.load_all()

    airport = db.get_airport(ident)

    if airport is None:
        raise SystemExit(f"Airport not found: {ident}")

    print()
    print(f"{airport.ident} - {airport.name}")
    print("-" * 70)
    print(f"Type:      {airport.type}")
    print(f"Lat/Lon:   {airport.lat_deg:.5f}, {airport.lon_deg:.5f}")
    print(f"Elev:      {airport.elevation_ft:.0f} ft")

    print()
    print("Runways:")
    for runway in db.get_runways(ident):
        print(
            f"  {runway.le_ident}/{runway.he_ident}  "
            f"{runway.length_ft:.0f} x {runway.width_ft:.0f} ft  "
            f"{runway.surface}  "
            f"HDG {runway.le_heading_deg:.0f}/{runway.he_heading_deg:.0f}"
        )

    print()
    print("Frequencies:")
    for freq in db.get_frequencies(ident):
        print(
            f"  {freq.type:<8} "
            f"{freq.frequency_mhz:.3f}  "
            f"{freq.description}"
        )

    print()


if __name__ == "__main__":
    main()