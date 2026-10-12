#!/usr/bin/env bash
# One-shot broad regression suite and ARM64 launch for V15 simulator ONLY.
set -euo pipefail
cd "$(dirname "$0")"
python -m pytest -q --no-cov \
  tests/user/blake_pfd/test_v15_stabilization.py \
  tests/user/blake_pfd/test_v14_cincinnati_performance.py \
  tests/user/blake_pfd/test_v13_cincinnati_moving.py \
  tests/user/blake_pfd/test_v12_ridge_depth.py \
  tests/user/blake_pfd/test_scenic_route_motion.py \
  tests/user/blake_pfd/test_terrain_integration.py \
  tests/user/blake_pfd/test_obstacle_projection.py \
  tests/user/blake_pfd/test_pfd_synthetic_obstacles.py \
  tests/user/blake_pfd/test_obstacle_integration.py
printf '\nPASS: consolidated V15 regression set. Launching simulator.\n'
bash run_blake_pfd_stable_v15.sh "${1:-cincinnati-fast}"
