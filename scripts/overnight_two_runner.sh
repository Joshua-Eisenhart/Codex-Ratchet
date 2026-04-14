#!/bin/bash
# overnight_two_runner.sh -- two-runner topology replacement for overnight_8h_run.sh
# Lane A (gated tool-sims) and Lane B (classical_baseline, ungated) run as
# independent background pools, each claiming from its own queue directory.
set -uo pipefail

ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
PY="${PY:-/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3}"
LOCK="/tmp/codex_ratchet_overnight.lock"
QUEUE_CLAIM="$ROOT/scripts/queue_claim.py"
GATE="$ROOT/scripts/verify_load_bearing_has_capability_probe.py"
LANE_A_DIR="$ROOT/system_v4/probes/a2_state/queue/lane_A"
LANE_B_DIR="$ROOT/system_v4/probes/a2_state/queue/lane_B"
LOG_DIR="$ROOT/overnight_logs"
STAMP=$(date +%Y%m%d_%H%M%S)

MINUTES=0
K1=2
K2=4
DRY=0

usage() { echo "usage: $0 --minutes N [--lane-a-parallel K1] [--lane-b-parallel K2] [--dry]"; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --minutes) MINUTES="$2"; shift 2 ;;
    --lane-a-parallel) K1="$2"; shift 2 ;;
    --lane-b-parallel) K2="$2"; shift 2 ;;
    --dry) DRY=1; shift ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $1"; usage ;;
  esac
done
[ "$MINUTES" -gt 0 ] 2>/dev/null || usage

mkdir -p "$LOG_DIR"
MANIFEST="$LOG_DIR/queue_manifest_${STAMP}.json"
DENIALS="$LOG_DIR/gate_denials_${STAMP}.json"
TOOLSTATE="$LOG_DIR/tool_capability_state_${STAMP}.json"
SUCCESS="$LOG_DIR/success_eval_${STAMP}.json"
EVENTS="$LOG_DIR/events_${STAMP}.ndjson"
: > "$EVENTS"

say()  { printf '[%s] %s\n' "$(date -Iseconds)" "$*"; }
emit() { # emit JSON event line
  local kind="$1"; shift
  printf '{"ts":"%s","kind":"%s",%s}\n' "$(date -Iseconds)" "$kind" "$*" >> "$EVENTS"
}

run_or_echo() { if [ "$DRY" -eq 1 ]; then echo "DRY: $*"; else "$@"; fi; }

# --- atomic O_EXCL lock via python ------------------------------------------
acquire_lock() {
  "$PY" - "$LOCK" <<'PY' || return 1
import os, sys
p = sys.argv[1]
try:
    fd = os.open(p, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o644)
except FileExistsError:
    print(f"LOCK HELD: {p}", file=sys.stderr); sys.exit(1)
os.write(fd, f"{os.getppid()}\n".encode()); os.close(fd)
PY
}
release_lock() { rm -f "$LOCK"; }

# --- worker: claim one item, maybe-gate, run, complete ----------------------
worker_once() { # $1=lane $2=queue_dir $3=gated(0/1) $4=worker_id
  local lane="$1" qdir="$2" gated="$3" wid="$4"
  local claim_json claim_path sim exit_code artifact sha
  if [ "$DRY" -eq 1 ]; then
    echo "DRY: $PY $QUEUE_CLAIM claim --queue $qdir --worker $wid"
    echo "DRY:  (gate if lane_a) $PY $GATE --sim <path>"
    echo "DRY:  run sim, then $PY $QUEUE_CLAIM complete --worker $wid"
    return 1  # signal empty to stop dry loop
  fi
  claim_json=$("$PY" "$QUEUE_CLAIM" claim --queue "$qdir" --worker "$wid" 2>/dev/null) || return 1
  [ -z "$claim_json" ] && return 1
  claim_path=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1]).get('claim_path',''))" "$claim_json")
  sim=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1]).get('sim',''))" "$claim_json")
  [ -z "$claim_path" ] && return 1
  [ -z "$sim" ] && return 1

  if [ "$gated" -eq 1 ]; then
    if ! "$PY" "$GATE" --sim "$sim" >/dev/null 2>&1; then
      "$PY" "$QUEUE_CLAIM" block --claim-path "$claim_path" --reason "gate_denied" >/dev/null 2>&1 || true
      emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\""
      return 0
    fi
  fi

  artifact="$LOG_DIR/artifact_${wid}_$(basename "$sim" .py)_$(date +%s).log"
  MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba \
    "$PY" "$sim" >"$artifact" 2>&1
  exit_code=$?
  sha=$(shasum -a 256 "$artifact" | awk '{print $1}')
  "$PY" "$QUEUE_CLAIM" complete --claim-path "$claim_path" --exit "$exit_code" --artifact "$artifact" >/dev/null 2>&1 || true
  emit claimed "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"exit\":$exit_code,\"artifact\":\"$artifact\",\"sha256\":\"$sha\""
  return 0
}

worker_loop() { # $1=lane $2=qdir $3=gated $4=wid $5=end_ts
  local lane="$1" qdir="$2" gated="$3" wid="$4" end_ts="$5"
  while [ "$(date +%s)" -lt "$end_ts" ]; do
    worker_once "$lane" "$qdir" "$gated" "$wid" || { [ "$DRY" -eq 1 ] && return 0; sleep 5; }
  done
}

# --- morning reports --------------------------------------------------------
write_reports() {
  EVENTS_PATH="$EVENTS" MANIFEST_PATH="$MANIFEST" DENIALS_PATH="$DENIALS" \
  TOOLSTATE_PATH="$TOOLSTATE" SUCCESS_PATH="$SUCCESS" ROOT="$ROOT" \
  "$PY" - <<'PY'
import json, os, hashlib, glob
from pathlib import Path
root = Path(os.environ["ROOT"])
events = [json.loads(l) for l in Path(os.environ["EVENTS_PATH"]).read_text().splitlines() if l.strip()]
claimed = [e for e in events if e["kind"] == "claimed"]
denied  = [e for e in events if e["kind"] == "gate_denied"]
Path(os.environ["MANIFEST_PATH"]).write_text(json.dumps(claimed, indent=2))
Path(os.environ["DENIALS_PATH"]).write_text(json.dumps(denied, indent=2))

# tool capability state: scan known tool probes
tool_probe_dir = root / "system_v4" / "probes"
tools = {}
for name in ["z3", "cvc5", "sympy", "toponetx", "pyg", "clifford"]:
    hits = list(tool_probe_dir.glob(f"*{name}*capability*.py")) + list(tool_probe_dir.glob(f"sim_{name}*.py"))
    probe = str(hits[0]) if hits else None
    result_hits = sorted((tool_probe_dir / "a2_state" / "sim_results").glob(f"*{name}*_results.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0) if (tool_probe_dir / "a2_state" / "sim_results").exists() else []
    latest = result_hits[-1] if result_hits else None
    sha = hashlib.sha256(latest.read_bytes()).hexdigest() if latest else None
    all_pass = None
    if latest:
        try:
            j = json.loads(latest.read_text())
            all_pass = bool(j.get("summary", {}).get("ok")) if isinstance(j.get("summary"), dict) else None
        except Exception:
            all_pass = None
    tools[name] = {"probe_exists": bool(probe), "probe": probe,
                   "latest_result": str(latest) if latest else None,
                   "latest_sha256": sha, "all_pass": all_pass}
Path(os.environ["TOOLSTATE_PATH"]).write_text(json.dumps(tools, indent=2))

lane_a = [e for e in claimed if e.get("lane") == "A"]
lane_b = [e for e in claimed if e.get("lane") == "B"]
summary = {
    "lane_a": {"claimed": len(lane_a),
               "pass": sum(1 for e in lane_a if e["exit"] == 0),
               "fail": sum(1 for e in lane_a if e["exit"] != 0),
               "gate_denied": len(denied)},
    "lane_b": {"claimed": len(lane_b),
               "pass": sum(1 for e in lane_b if e["exit"] == 0),
               "fail": sum(1 for e in lane_b if e["exit"] != 0)},
    "total_events": len(events),
}
Path(os.environ["SUCCESS_PATH"]).write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PY
}

# --- main -------------------------------------------------------------------
say "two-runner start minutes=$MINUTES K1=$K1 K2=$K2 dry=$DRY"

if [ "$DRY" -eq 1 ]; then
  echo "DRY: acquire_lock $LOCK"
  echo "DRY: spawn $K1 Lane A workers loop(claim lane_A -> gate -> run -> complete) until $MINUTES min"
  echo "DRY: spawn $K2 Lane B workers loop(claim lane_B -> run -> complete) until $MINUTES min"
  for i in $(seq 1 "$K1"); do worker_once "A" "$LANE_A_DIR" 1 "laneA_w${i}" || true; done
  for i in $(seq 1 "$K2"); do worker_once "B" "$LANE_B_DIR" 0 "laneB_w${i}" || true; done
  echo "DRY: wait for pools, then write reports:"
  echo "DRY:  $MANIFEST"
  echo "DRY:  $DENIALS"
  echo "DRY:  $TOOLSTATE"
  echo "DRY:  $SUCCESS"
  exit 0
fi

acquire_lock || { say "FAILED to acquire $LOCK"; exit 1; }
trap 'release_lock' EXIT

END_TS=$(( $(date +%s) + MINUTES * 60 ))
pids=()
for i in $(seq 1 "$K1"); do
  worker_loop "A" "$LANE_A_DIR" 1 "laneA_w${i}" "$END_TS" &
  pids+=("$!")
done
for i in $(seq 1 "$K2"); do
  worker_loop "B" "$LANE_B_DIR" 0 "laneB_w${i}" "$END_TS" &
  pids+=("$!")
done
say "spawned ${#pids[@]} workers; budget ends $(date -r "$END_TS" -Iseconds 2>/dev/null || date -Iseconds)"

# wait for budget, then graceful shutdown
while [ "$(date +%s)" -lt "$END_TS" ]; do sleep 30; done
say "budget expired; terminating pools"
for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done
sleep 3
for p in "${pids[@]}"; do kill -9 "$p" 2>/dev/null || true; done
wait 2>/dev/null || true

write_reports
say "reports written: $MANIFEST $DENIALS $TOOLSTATE $SUCCESS"
