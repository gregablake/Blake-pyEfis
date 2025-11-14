"""
Stratux to FIX Gateway bridge script
- Reads Stratux JSON (default: http://192.168.10.1/getSituation)
- Publishes GPS/attitude to FIX Gateway keys expected by pyEfis
- Requires: requests, fix (FIX Gateway Python client, if available)
- Edit STRATUX_URL and FIX_GATEWAY_HOST as needed
"""
import time
import requests
import sys

# If you have a fix client library, import it here
try:
    import fix
except ImportError:
    fix = None  # Replace with your FIX Gateway client logic

STRATUX_URL = "http://192.168.10.1/getSituation"  # Default Stratux IP
POLL_INTERVAL = 1.0  # seconds

# Map Stratux JSON fields to FIX keys
FIELD_MAP = {
    "GPSLatitude": "LAT",
    "GPSLongitude": "LONG",
    "GPSAltitude": "ALT",
    "GPSSpeed": "GS",  # Ground speed (knots)
    "GPSCourse": "HEAD",  # Magnetic heading
    "BaroPressure": "BARO",  # Inches Hg
    # Add more mappings as needed
}

def publish_to_fix(key, value):
    if fix:
        try:
            fix.db.set_value(key, value)
        except Exception as e:
            print(f"FIX set_value error: {e}")
    else:
        print(f"[SIM] Would set {key} = {value}")

def main():
    print("Starting Stratux to FIX Gateway bridge...")
    while True:
        try:
            resp = requests.get(STRATUX_URL, timeout=2)
            data = resp.json()
            for stratux_field, fix_key in FIELD_MAP.items():
                value = data.get(stratux_field)
                if value is not None:
                    publish_to_fix(fix_key, value)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
