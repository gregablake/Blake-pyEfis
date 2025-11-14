"""
Stratux to FIX Gateway bridge (traffic visualization)
- Publishes a list of nearby traffic (bearing, distance) to a FIX key
- For use with a custom traffic gauge on the PFD/AHRS screen
- Requires: requests, fix (FIX Gateway Python client, if available)
"""
import time
import requests
import math
import json

try:
    import fix
except ImportError:
    fix = None

STRATUX_URL = "http://192.168.10.1/getSituation"
TRAFFIC_URL = "http://192.168.10.1/getTraffic"
POLL_INTERVAL = 1.0
TRAFFIC_KEY = "STRATUX_TRAFFIC_LIST"

# Helper: calculate bearing from ownship to traffic
# lat/lon in degrees, returns bearing in degrees

def bearing(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    brng = math.atan2(y, x)
    brng = math.degrees(brng)
    return (brng + 360) % 360

def publish_to_fix(key, value):
    if fix:
        try:
            fix.db.set_value(key, value)
        except Exception as e:
            print(f"FIX set_value error: {e}")
    else:
        print(f"[SIM] Would set {key} = {value}")

def main():
    print("Starting Stratux traffic bridge...")
    while True:
        try:
            situation = requests.get(STRATUX_URL, timeout=2).json()
            traffic = requests.get(TRAFFIC_URL, timeout=2).json()
            own_lat = situation.get("GPSLatitude")
            own_lon = situation.get("GPSLongitude")
            own_alt = situation.get("GPSAltitude")
            traffic_list = []
            if own_lat is not None and own_lon is not None and isinstance(traffic, list):
                for t in traffic:
                    t_lat = t.get("Lat")
                    t_lon = t.get("Lng")
                    t_alt = t.get("Alt")
                    t_dist = t.get("DistanceNm")
                    t_id = t.get("Icao_addr")
                    if t_lat is not None and t_lon is not None and t_dist is not None:
                        brg = bearing(own_lat, own_lon, t_lat, t_lon)
                        rel_alt = (t_alt - own_alt) if (t_alt is not None and own_alt is not None) else None
                        traffic_list.append({
                            "id": t_id,
                            "bearing": round(brg, 1),
                            "distance": round(t_dist, 2),
                            "rel_alt": rel_alt
                        })
            # Publish as JSON string (FIX Gateway may only support string values)
            publish_to_fix(TRAFFIC_KEY, json.dumps(traffic_list))
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
