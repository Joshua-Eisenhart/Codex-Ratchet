#!/usr/bin/env bash
set -euo pipefail

PY="/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
ROOT="system_v8/manifold"
ENGINE="$ROOT/engine"
RESULTS="$ROOT/results"
OUT="$RESULTS/deep_alt"

export PYTHONDONTWRITEBYTECODE=1

mkdir -p "$OUT"

"$PY" "$ENGINE/connection_layer_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$RESULTS/whole_manifold.json" \
  --output "$OUT/connection_alt.json"

"$PY" "$ENGINE/history_layer_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$OUT/connection_alt.json" \
  --output "$OUT/history_alt.json"

"$PY" "$ENGINE/persistence_layer_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$OUT/history_alt.json" \
  --output "$OUT/persistence_alt.json"

"$PY" "$ENGINE/chirality_layer_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$OUT/persistence_alt.json" \
  --output "$OUT/chirality_alt.json"

"$PY" "$ENGINE/whole_manifold_v2_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$OUT" \
  --output "$OUT/whole_manifold_v2_alt.json"

"$PY" "$ENGINE/verify_deep_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$OUT" \
  --output "$OUT/verification_alt.json"

"$PY" "$ENGINE/deterministic_replay_deep_alt.py" \
  --source "$RESULTS/source_packets.json" \
  --prior "$OUT" \
  --output "$OUT/deterministic_replay_deep_alt.json"
