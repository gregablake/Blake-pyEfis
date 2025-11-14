"""
Stratux to FIX Gateway bridge (extended)
- Reads Stratux JSON for GPS, AHRS, weather, and traffic
- Publishes to FIX keys for pyEfis
- Simulates radar/traffic alert as a single status key
- Requires: requests, fix (FIX Gateway Python client, if available)
"""
import time
import requests
import sys

try:
    import fix
except ImportError:
    fix = None

STRATUX_URL = "http://192.168.10.1/getSituation"
TRAFFIC_URL = "http://192.168.10.1/getTraffic"
WEATHER_URL = "http://192.168.10.1/getWeather"
POLL_INTERVAL = 1.0

FIELD_MAP = {
    # Situation (AHRS/GPS)
    "GPSLatitude": "LAT",
    "GPSLongitude": "LONG",
    "GPSAltitude": "ALT",
    "GPSSpeed": "GS",
    "GPSCourse": "HEAD",
    "BaroPressure": "BARO",
    "Pitch": "PITCH",
    "Roll": "ROLL",
    "Yaw": "YAW",
    # Add more as needed
}

# These keys will be used for alert/status
STRATUX_RADAR_ALERT_KEY = "STRATUX_RADAR_ALERT"
STRATUX_TRAFFIC_ALERT_KEY = "STRATUX_TRAFFIC_ALERT"
STRATUX_STATUS_KEY = "STRATUX_STATUS"


def publish_to_fix(key, value):
    if fix:
        try:
            fix.db.set_value(key, value)
        except Exception as e:
            print(f"FIX set_value error: {e}")
    else:
        print(f"[SIM] Would set {key} = {value}")

def get_json(url):
    try:
        resp = requests.get(url, timeout=2)
        return resp.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    print("Starting extended Stratux to FIX Gateway bridge...")
    while True:
        # Situation (AHRS/GPS)
        situation = get_json(STRATUX_URL)
        if situation:
            for stratux_field, fix_key in FIELD_MAP.items():
                value = situation.get(stratux_field)
                if value is not None:
                    publish_to_fix(fix_key, value)
        # Traffic
        traffic = get_json(TRAFFIC_URL)
        traffic_alert = 0
        if traffic and isinstance(traffic, list):
            # Simple alert: 1 if any traffic is within 2nm and 1000ft
            for t in traffic:
                dist = t.get("DistanceNm")
                alt_diff = abs(t.get("Alt", 0) - situation.get("GPSAltitude", 0)) if situation else 9999
                if dist is not None and dist < 2.0 and alt_diff < 1000:
                    traffic_alert = 1
                    break
            publish_to_fix(STRATUX_TRAFFIC_ALERT_KEY, traffic_alert)
        # Weather
        weather = get_json(WEATHER_URL)
        radar_alert = 0
        if weather and "METARs" in weather:
            # Example: set alert if any METAR reports precipitation
            for metar in weather["METARs"]:
                if "RA" in metar.get("Raw-Report", "") or "SN" in metar.get("Raw-Report", ""):
                    radar_alert = 1
                    break
            publish_to_fix(STRATUX_RADAR_ALERT_KEY, radar_alert)
        # Combined status (for a single gauge)
        status = 0
        if traffic_alert:
            status += 1
        if radar_alert:
            status += 2
        publish_to_fix(STRATUX_STATUS_KEY, status)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
