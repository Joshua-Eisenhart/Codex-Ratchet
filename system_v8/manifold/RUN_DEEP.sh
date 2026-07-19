#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0

SIM_PYTHON=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
MANIFOLD=system_v8/manifold
ENGINE=${MANIFOLD}/engine
RESULTS=${MANIFOLD}/results
DEEP_RESULTS=${RESULTS}/deep

mkdir -p "${DEEP_RESULTS}"

"${SIM_PYTHON}" "${ENGINE}/connection_layer.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${RESULTS}/whole_manifold.json" \
  --output "${DEEP_RESULTS}/connection.json"

"${SIM_PYTHON}" "${ENGINE}/history_layer.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${DEEP_RESULTS}/connection.json" \
  --output "${DEEP_RESULTS}/history.json"

"${SIM_PYTHON}" "${ENGINE}/persistence_layer.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${DEEP_RESULTS}/history.json" \
  --output "${DEEP_RESULTS}/persistence.json"

"${SIM_PYTHON}" "${ENGINE}/chirality_layer.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${DEEP_RESULTS}/persistence.json" \
  --output "${DEEP_RESULTS}/chirality.json"

"${SIM_PYTHON}" "${ENGINE}/whole_manifold_v2.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${DEEP_RESULTS}/chirality.json" \
  --output "${DEEP_RESULTS}/whole_manifold_v2.json"

"${SIM_PYTHON}" "${ENGINE}/verify_deep.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${DEEP_RESULTS}" \
  --output "${DEEP_RESULTS}/verification.json"

"${SIM_PYTHON}" "${ENGINE}/deterministic_replay_deep.py" \
  --source "${RESULTS}/source_packets.json" \
  --prior "${DEEP_RESULTS}" \
  --output "${DEEP_RESULTS}/deterministic_replay.json"
