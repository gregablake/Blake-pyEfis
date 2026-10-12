#!/usr/bin/env bash
# V15 consolidated REAL TERRAIN camera comparison: Cincinnati moving route or Rocky Mountain static.
# NOT FOR FLIGHT. No Docker rebuild; source files are read-only bind mounted.
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-cincinnati-fast}"
if [[ "$MODE" != "cincinnati" && "$MODE" != "cincinnati-depth" && "$MODE" != "cincinnati-fast" && "$MODE" != "mountain" && "$MODE" != "ridge" && "$MODE" != "ridge-high" ]]; then
  echo "Usage: bash run_blake_pfd_stable_v15.sh [cincinnati|cincinnati-depth|cincinnati-fast|mountain|ridge|ridge-high]" >&2
  exit 2
fi
DATA="$HOME/.local/share/blake_pyefis"
CFG="$DATA/pfd_config.srtm_sim.yaml"
for file in "$DATA/obstacles.sqlite" "$CFG" "$DATA/terrain/N39W085.hgt" "$DATA/terrain/N38W085.hgt" \
  src/pyefis/user/blake_pfd/pfd_demo.py src/pyefis/user/blake_pfd/sensors_sim.py \
  src/pyefis/user/blake_pfd/core/obstacle_projection.py; do
  if [[ ! -f "$file" ]]; then
    echo "MISSING REQUIRED FILE: $file" >&2
    exit 1
  fi
done
if ! docker image inspect blake-pfd-cm5:latest >/dev/null 2>&1; then
  echo "MISSING DOCKER IMAGE: blake-pfd-cm5:latest" >&2
  exit 1
fi
SCENIC=1
MOUNTAIN=0
if [[ "$MODE" == "mountain" || "$MODE" == "ridge" || "$MODE" == "ridge-high" ]]; then
  SCENIC=0
  MOUNTAIN=1
  # Uses ONLY actual Mapzen Skadi elevation data. Rejects missing/malformed
  # tiles instead of displaying a fictional mountainous landscape.
  python3 - "$DATA/terrain" <<'PYTILE'
from pathlib import Path
import gzip
import os
import sys
import tempfile
from urllib.request import urlopen
root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=True)
tile = root / 'N40W106.hgt'
allowed_sizes = {2 * 1201**2, 2 * 3601**2}
if tile.is_file() and tile.stat().st_size in allowed_sizes:
    print('PASS: Existing real Rocky Mountain SRTM tile:', tile, flush=True)
else:
    if tile.exists():
        raise SystemExit('Invalid existing N40W106.hgt tile. Stopping without overwrite.')
    url = 'https://s3.amazonaws.com/elevation-tiles-prod/skadi/N40/N40W106.hgt.gz'
    print('Downloading real Rocky Mountain SRTM tile:', url, flush=True)
    with urlopen(url, timeout=90) as response:
        compressed = response.read(40_000_001)
    if len(compressed) > 40_000_000:
        raise SystemExit('Terrain download exceeded 40 MB limit.')
    data = gzip.decompress(compressed)
    if len(data) not in allowed_sizes:
        raise SystemExit('Downloaded terrain tile has invalid dimensions.')
    fd, path = tempfile.mkstemp(prefix='.N40W106.', dir=root)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
        os.replace(path, tile)
    finally:
        if os.path.exists(path):
            os.unlink(path)
    print('PASS: Validated real SRTM tile:', tile, flush=True)
PYTILE
fi
# Codespaces sometimes loses ARM64 binfmt registrations between sessions.
# Check the existing image before launching; repair only when necessary.
if ! docker run --rm --platform linux/arm64 --entrypoint /bin/sh \
       blake-pfd-cm5:latest -c 'test "$(uname -m)" = "aarch64"' \
       >/dev/null 2>&1; then
  echo 'ARM64 interpreter missing; attempting QEMU/binfmt re-registration.'
  docker run --privileged --rm tonistiigi/binfmt --install arm64
  docker run --rm --platform linux/arm64 --entrypoint /bin/sh \
       blake-pfd-cm5:latest -c 'test "$(uname -m)" = "aarch64"'
fi
printf '\nRunning V15 %s REAL-TERRAIN scene (NOT FOR FLIGHT).\n' "$MODE"
if [[ "$MODE" == "mountain" || "$MODE" == "ridge" || "$MODE" == "ridge-high" ]]; then
  printf 'STATIC mountain camera scene; live KHAO route is HIDDEN.\n'
fi
printf 'Open forwarded Codespaces port 6080. Ctrl+C stops this container.\n'
docker rm -f blake-pfd-test >/dev/null 2>&1 || true
exec docker run --platform linux/arm64 --rm -it -p 6080:6080 \
  -e BLAKE_PFD_V14_OPTIMIZE="$( [[ "$MODE" == "cincinnati-fast" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V14_PROFILE="$( [[ "$MODE" == "cincinnati" || "$MODE" == "cincinnati-depth" || "$MODE" == "cincinnati-fast" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V15_LOG_METRICS="$( [[ "$MODE" == "cincinnati-fast" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V13_CINCINNATI_DEPTH="$( [[ "$MODE" == "cincinnati-depth" || "$MODE" == "cincinnati-fast" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V13_CINCINNATI_DIAGNOSTICS="$( [[ "$MODE" == "cincinnati" || "$MODE" == "cincinnati-depth" || "$MODE" == "cincinnati-fast" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_SCENIC_DEMO="$SCENIC" \
  -e BLAKE_PFD_MOUNTAIN_DEMO="$MOUNTAIN" \
  -e BLAKE_PFD_V4_SCENIC_VISUALS=1 \
  -e BLAKE_PFD_V5_REAL_RELIEF=1 \
  -e BLAKE_PFD_V6_VISUALS=1 \
  -e BLAKE_PFD_V7_VISUALS=1 \
  -e BLAKE_PFD_V8_RIDGE_DEMO="$( [[ "$MODE" == "ridge" || "$MODE" == "ridge-high" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V10_RIDGE_VISUALS="$( [[ "$MODE" == "ridge" || "$MODE" == "ridge-high" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V11_RIDGE_SHADING="$( [[ "$MODE" == "ridge" || "$MODE" == "ridge-high" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V12_RIDGE_DEPTH="$( [[ "$MODE" == "ridge" || "$MODE" == "ridge-high" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V9_HIGH_RIDGE="$( [[ "$MODE" == "ridge-high" ]] && echo 1 || echo 0 )" \
  -e BLAKE_PFD_V5_CONTOURS="${BLAKE_PFD_V5_CONTOURS:-0}" \
  -v "$DATA:/root/.local/share/blake_pyefis:ro" \
  -v "$CFG:/app/src/pyefis/user/blake_pfd/pfd_config.yaml:ro" \
  -v "$PWD/src/pyefis/user/blake_pfd/pfd_demo.py:/app/src/pyefis/user/blake_pfd/pfd_demo.py:ro" \
  -v "$PWD/src/pyefis/user/blake_pfd/sensors_sim.py:/app/src/pyefis/user/blake_pfd/sensors_sim.py:ro" \
  -v "$PWD/src/pyefis/user/blake_pfd/core/obstacle_projection.py:/app/src/pyefis/user/blake_pfd/core/obstacle_projection.py:ro" \
  --name blake-pfd-test blake-pfd-cm5:latest bash -lc \
  'Xvfb :99 -screen 0 1024x600x24 >/tmp/xvfb.log 2>&1 & sleep 2; x11vnc -display :99 -forever -shared -nopw -rfbport 5900 >/tmp/x11vnc.log 2>&1 & websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 & export DISPLAY=:99; exec /app/.venv/bin/python -m pyefis.user.blake_pfd.pfd_demo'
