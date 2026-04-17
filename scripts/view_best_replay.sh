#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/view_best_replay.sh <sim_name> [--consumer <name>] [extra args...]" >&2
  echo "example: scripts/view_best_replay.sh hopf_bundle_lift --consumer viewer_surface_smoke --off-screen-smoke --dry-run" >&2
  exit 2
fi

SIM_NAME="$1"
shift

TRANSPORT_ROOT="${VIZ_RUN_ROOT_TRANSPORT:-/tmp/viz_runs_transport}"
HOPF_ROOT="${VIZ_RUN_ROOT_HOPF:-/tmp/viz_runs_hopf}"
VIEWER_PYTHON="${VIZ_VIEWER_PYTHON:-}"

ARGS=(
  python3 -m system_v4.visualization.cli
  view-best-run
  --root "${TRANSPORT_ROOT}"
  --root "${HOPF_ROOT}"
  --sim "${SIM_NAME}"
)

if [[ -n "${VIEWER_PYTHON}" ]]; then
  ARGS+=(--python-executable "${VIEWER_PYTHON}")
fi

exec "${ARGS[@]}" "$@"
