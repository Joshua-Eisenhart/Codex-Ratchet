#!/bin/bash
# overnight_two_runner.sh -- two-runner topology replacement for overnight_8h_run.sh
# Lane A (gated tool-sims) and Lane B (classical_baseline, ungated) run as
# independent background pools, each claiming from its own queue directory.
set -uo pipefail

ROOT="${CODEX_RATCHET_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}"
PY="${CODEX_RATCHET_PYTHON:-${SIM_PY:-${PY:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}}}"
LOCK="/tmp/codex_ratchet_overnight.lock"
LOCK_META="/tmp/codex_ratchet_overnight.lock.meta"
RUNNER_COMMAND_GREP="overnight_two_runner.sh"
QUEUE_CLAIM="$ROOT/scripts/queue_claim.py"
GATE="$ROOT/scripts/verify_load_bearing_has_capability_probe.py"
SEMANTIC_GUARD="$ROOT/scripts/direct_sim_semantic_guard.py"
LANE_A_DIR="$ROOT/system_v4/probes/a2_state/queue/lane_A"
LANE_B_DIR="$ROOT/system_v4/probes/a2_state/queue/lane_B"
RESULTS="$ROOT/system_v4/probes/a2_state/sim_results"
STAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="${LOG_DIR:-$ROOT/overnight_logs}"
TRACKED_REPAIR_REPORT_DIR="${TRACKED_REPAIR_REPORT_DIR:-$ROOT/system_v5/ops/queue_cleanup}"

MINUTES=0
K1=2
K2=4
DRY=0
STRICT_RECEIPT_ADMISSION="${STRICT_RECEIPT_ADMISSION:-1}"
STRICT_WIZARD_QUEUE_ADMISSION="${STRICT_WIZARD_QUEUE_ADMISSION:-1}"
ALLOW_HELPER_PROCESSES="${ALLOW_HELPER_PROCESSES:-0}"
ADMISSION_BYPASS_SENTINEL="${ADMISSION_BYPASS_SENTINEL:-$ROOT/system_v5/ops/.allow_admission_bypass_recovery}"
ALLOW_ADMISSION_BYPASS_RECOVERY="${ALLOW_ADMISSION_BYPASS_RECOVERY:-0}"
SIM_TIMEOUT=900  # seconds; kill any single sim that runs longer than this

# Sims that must never enter the overnight queue (meta-benchmarks, harnesses).
QUEUE_BLACKLIST="sim_timing_benchmark.py|autoresearch_sim_harness.py|exploratory_process_cycle_stage_matrix_sim.py|stage_matrix_neg_lib.py"
LATE_STAGE_PATTERN='tier_d|boundary_flux|bridge|coupling|pairwise|coexistence|rho_ab|phi0|emergence|axis|axis0|bipartite|entanglement|mutual_information|mutual_info|coherent_information|coherent_info|concurrence|negativity|schmidt|entropy|capacity|capacities|carnot|szilard|landauer|thermo'

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

if [ "$DRY" -eq 1 ]; then
  LOG_DIR="${DRY_LOG_DIR:-/tmp/codex_ratchet_overnight_dry}"
  TRACKED_REPAIR_REPORT_DIR="${DRY_REPAIR_REPORT_DIR:-/tmp/codex_ratchet_overnight_dry/queue_cleanup}"
fi

mkdir -p "$LOG_DIR"
mkdir -p "$TRACKED_REPAIR_REPORT_DIR"
MANIFEST="$LOG_DIR/queue_manifest_${STAMP}.json"
DENIALS="$LOG_DIR/gate_denials_${STAMP}.json"
TOOLSTATE="$LOG_DIR/tool_capability_state_${STAMP}.json"
SUCCESS="$LOG_DIR/success_eval_${STAMP}.json"
DUP_REPAIR_REPORT="$LOG_DIR/queue_done_duplicate_repair_${STAMP}.json"
DUP_REPAIR_REPORT_TRACKED="$TRACKED_REPAIR_REPORT_DIR/queue_done_duplicate_repair_${STAMP}.json"
EVENTS="$LOG_DIR/events_${STAMP}.ndjson"
: > "$EVENTS"

say()  { printf '[%s] %s\n' "$(date -Iseconds)" "$*"; }
emit() { # emit JSON event line
  local kind="$1"; shift
  printf '{"ts":"%s","kind":"%s",%s}\n' "$(date -Iseconds)" "$kind" "$*" >> "$EVENTS"
}

run_or_echo() { if [ "$DRY" -eq 1 ]; then echo "DRY: $*"; else "$@"; fi; }

helper_process_preflight() {
  if [ "$ALLOW_HELPER_PROCESSES" = "1" ]; then
    say "Helper process preflight bypassed by ALLOW_HELPER_PROCESSES=1"
    return 0
  fi
  "$PY" "$ROOT/scripts/helper_process_audit.py" --strict >/dev/null
}

is_overnight_process() {
  local pid="$1"
  [ -n "$pid" ] || return 1
  local cmd
  cmd="$(ps -p "$pid" -o command= 2>/dev/null | tr -d '\r')"
  case "$cmd" in
    *"$RUNNER_COMMAND_GREP"*) return 0 ;;
    *) return 1 ;;
  esac
}

assert_single_controller_preflight() {
  local pid others=0
  local current_pid="$$"
  for pid in $(pgrep -f "overnight_two_runner\\.sh" 2>/dev/null || true); do
    [ -z "$pid" ] && continue
    [ "$pid" = "$current_pid" ] && continue
    if is_overnight_process "$pid"; then
      others=$((others + 1))
      say "Another overnight_two_runner controller is already active (pid=$pid)."
    fi
  done
  [ "$others" -eq 0 ]
}

admission_bypass_preflight() {
  if [ "$STRICT_RECEIPT_ADMISSION" = "1" ] && [ "$STRICT_WIZARD_QUEUE_ADMISSION" = "1" ]; then
    if [ -f "$ADMISSION_BYPASS_SENTINEL" ] && [ "$ALLOW_ADMISSION_BYPASS_RECOVERY" != "1" ]; then
      say "Admission bypass sentinel present at $ADMISSION_BYPASS_SENTINEL; blocked unless ALLOW_ADMISSION_BYPASS_RECOVERY=1."
      return 1
    fi
    return 0
  fi
  if [ "$ALLOW_ADMISSION_BYPASS_RECOVERY" = "1" ] && [ -f "$ADMISSION_BYPASS_SENTINEL" ]; then
    say "Recovery bypass allowed by ALLOW_ADMISSION_BYPASS_RECOVERY=1"
    return 0
  fi
  say "Admission bypass preflight failed: strict admission and wizard-queue gates are not both enabled."
  return 1
}

run_sim_with_timeout() { # $1=sim $2=artifact
  local sim="$1" artifact="$2"
  MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba \
    "$PY" - "$PY" "$sim" "$SIM_TIMEOUT" >"$artifact" 2>&1 <<'PY'
import subprocess
import sys

py = sys.argv[1]
sim = sys.argv[2]
timeout = int(sys.argv[3])

try:
    result = subprocess.run([py, sim], timeout=timeout, check=False)
except subprocess.TimeoutExpired:
    raise SystemExit(124)

raise SystemExit(result.returncode)
PY
  return $?
}

stage_gate_claim_for_sim() {
  local sim="$1" base
  if "$PY" - "$sim" "$RESULTS" >/dev/null 2>&1 <<'PY'
import json
import pathlib
import sys

sim = pathlib.Path(sys.argv[1])
results = pathlib.Path(sys.argv[2])
path = results / f"{sim.stem}_results.json"
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if payload.get("classification") == "tool_lego_fit_probe" and payload.get("promotion_allowed") is False:
    raise SystemExit(0)
raise SystemExit(1)
PY
  then
    return 1
  fi
  base=$(basename "$sim" .py)
  base=${base#sim_}
  case "$base" in
    classical_baseline_*) return 1 ;;
    *tier_d*|*boundary_flux*) echo "tier_d"; return 0 ;;
    *bridge*|*coupling*|*pairwise*|*coexistence*|*rho_ab*|*phi0*|*emergence*) echo "scientific_coupling"; return 0 ;;
    axis*|axis0*) echo "axis"; return 0 ;;
    *bipartite*|*entanglement*|*mutual_information*|*mutual_info*|*coherent_information*|*coherent_info*|*concurrence*|*negativity*|*schmidt*|*entropy*|*capacity*|*capacities*|*carnot*|*szilard*|*landauer*|*thermo*) echo "default_late_stage"; return 0 ;;
  esac
  return 1
}

stage_gate_allows_sim() {
  local sim="$1" claim
  claim=$(stage_gate_claim_for_sim "$sim") || return 0
  "$PY" "$ROOT/scripts/stage_gate.py" --claim "$claim" >/dev/null 2>&1
}

# --- atomic O_EXCL lock via python ------------------------------------------
is_pid_alive() {
  local pid="$1"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null
}

cleanup_orphan_lock() {
  [ -f "$LOCK" ] || return 0
  local holder
  holder=$(awk 'NR==1 {print $1}' "$LOCK" 2>/dev/null | tr -cd '0-9')
  if is_pid_alive "$holder" && is_overnight_process "$holder"; then
    return 1
  fi
  say "Removing stale overnight lock: $LOCK (holder=$holder)"
  rm -f "$LOCK"
  rm -f "$LOCK_META"
}

acquire_lock() {
  assert_single_controller_preflight || return 1
  cleanup_orphan_lock || return 1
  "$PY" - "$LOCK" "$$" <<'PY' || return 1
import os, sys
p = sys.argv[1]
pid = sys.argv[2]
try:
    fd = os.open(p, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o644)
except FileExistsError:
    print(f"LOCK HELD: {p}", file=sys.stderr); sys.exit(1)
os.write(fd, f"{pid}\n".encode()); os.close(fd)
PY
}

owns_lock() {
  local holder
  holder=$(awk 'NR==1 {print $1}' "$LOCK" 2>/dev/null | tr -cd '0-9')
  [ "$holder" = "$$" ] && return 0
  return 1
}

release_lock() {
  if [ -f "$LOCK" ] && ! owns_lock; then
    return 0
  fi
  rm -f "$LOCK"
  rm -f "$LOCK_META"
}

record_lock_meta() {
  cat > "$LOCK_META" <<EOF
{
  "pid": $$,
  "started_at": "$(date -Iseconds)",
  "command": "$0 --minutes $MINUTES --lane-a-parallel $K1 --lane-b-parallel $K2",
  "host": "$(hostname)"
}
EOF
}

repair_duplicate_done_records() {
  emit duplicate_repair_queued "\"phase\":\"preflight\""
  local repair_mode="scan"
  local repair_stdout repair_stderr
  local -a repair_cmd
  repair_cmd=("$PY" "$ROOT/scripts/repair_queue_done_duplicates.py" --keep-newest --report-path "$DUP_REPAIR_REPORT_TRACKED")
  if [ "$DRY" -eq 0 ]; then
    repair_mode="apply"
    repair_cmd+=(--apply)
  fi
  repair_stdout="/tmp/codex_ratchet_duplicate_repair_${STAMP}.stdout"
  repair_stderr="/tmp/codex_ratchet_duplicate_repair_${STAMP}.stderr"
  if ! "${repair_cmd[@]}" > "$repair_stdout" 2>"$repair_stderr"; then
    say "FAILED duplicate-done repair preflight"
    [ -s "$repair_stderr" ] && tail -20 "$repair_stderr"
    return 1
  fi

  mkdir -p "$TRACKED_REPAIR_REPORT_DIR"
  cp "$DUP_REPAIR_REPORT_TRACKED" "$DUP_REPAIR_REPORT" 2>/dev/null || true

  local duplicates total_bases
  read -r duplicates total_bases < <("$PY" - "$DUP_REPAIR_REPORT_TRACKED" <<'PY'
import json, sys
report = json.loads(open(sys.argv[1], encoding="utf-8").read())
print(report.get("total_duplicate_files", 0), report.get("total_duplicate_bases", 0))
PY
)
  if [ "${duplicates:-0}" -gt 0 ]; then
    say "queue_done_duplicate_repair: $repair_mode completed with $duplicates duplicates across $total_bases ids"
    emit duplicate_repair_done "\"phase\":\"preflight\",\"mode\":\"$repair_mode\",\"duplicates\":$duplicates,\"bases\":$total_bases,\"report\":\"$DUP_REPAIR_REPORT_TRACKED\",\"legacy_report\":\"$DUP_REPAIR_REPORT\""
  else
    emit duplicate_repair_done "\"phase\":\"preflight\",\"mode\":\"$repair_mode\",\"duplicates\":0"
  fi
  return 0
}

stop_workers() {
  for p in "${pids[@]:-}"; do kill "$p" 2>/dev/null || true; done
  sleep 3
  for p in "${pids[@]:-}"; do kill -9 "$p" 2>/dev/null || true; done
  wait 2>/dev/null || true
}

cleanup() {
  stop_workers
  release_lock
}

# --- worker: claim one item, maybe-gate, run, complete ----------------------
worker_once() { # $1=lane $2=queue_dir $3=gated(0/1) $4=worker_id
  local lane="$1" qdir="$2" gated="$3" wid="$4"
  local claim_json claim_path sim exit_code artifact sha complete_json terminal_state blocked_reason
  if [ "$DRY" -eq 1 ]; then
    echo "DRY: $PY $QUEUE_CLAIM claim --queue $qdir --worker $wid"
    if [ "$gated" -eq 1 ]; then
      echo "DRY:  lane gate $PY $GATE --sim <path>"
    else
      echo "DRY:  no lane-specific capability gate"
    fi
    echo "DRY:  semantic guard $PY $SEMANTIC_GUARD --name <basename> --probes-dir $ROOT/system_v4/probes"
    echo "DRY:  run sim, then $PY $QUEUE_CLAIM complete --worker $wid"
    return 1  # signal empty to stop dry loop
  fi
  claim_json=$("$PY" "$QUEUE_CLAIM" claim --queue "$qdir" --worker "$wid" 2>/dev/null) || return 1
  [ -z "$claim_json" ] && return 1
  claim_path=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1]).get('claim_path',''))" "$claim_json")
  sim=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1]).get('sim',''))" "$claim_json")
  [ -z "$claim_path" ] && return 1
  [ -z "$sim" ] && return 1

  # Block blacklisted meta-sims (benchmarks/harnesses) that must never run as queue items.
  sim_base=$(basename "$sim")
  if echo "$sim_base" | grep -qE "^($QUEUE_BLACKLIST)$"; then
    "$PY" "$QUEUE_CLAIM" block --claim-path "$claim_path" --reason "blacklisted_meta_sim" >/dev/null 2>&1 || true
    emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"reason\":\"blacklisted\""
    return 0
  fi

  if ! stage_gate_allows_sim "$sim"; then
    "$PY" "$QUEUE_CLAIM" block --claim-path "$claim_path" --reason "stage_gate_blocked" >/dev/null 2>&1 || true
    emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"reason\":\"stage_gate_blocked\""
    return 0
  fi

  if ! "$PY" "$SEMANTIC_GUARD" --name "$(basename "$sim" .py)" --probes-dir "$ROOT/system_v4/probes" >/dev/null 2>&1; then
    "$PY" "$QUEUE_CLAIM" block --claim-path "$claim_path" --reason "semantic_name_blocked" >/dev/null 2>&1 || true
    emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"reason\":\"semantic_name_blocked\""
    return 0
  fi

  if [ "$STRICT_WIZARD_QUEUE_ADMISSION" = "1" ]; then
    if ! "$PY" "$ROOT/scripts/wizard_sim_admission.py" --basename "$(basename "$sim" .py)" --sim-path "$sim" >/dev/null 2>&1; then
      "$PY" "$QUEUE_CLAIM" block --claim-path "$claim_path" --reason "wizard_admission_blocked" >/dev/null 2>&1 || true
      emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"reason\":\"wizard_admission_blocked\""
      return 0
    fi
  fi

  if [ "$gated" -eq 1 ]; then
    if ! "$PY" "$GATE" --sim "$sim" >/dev/null 2>&1; then
      "$PY" "$QUEUE_CLAIM" block --claim-path "$claim_path" --reason "gate_denied" >/dev/null 2>&1 || true
      emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\""
      return 0
    fi
  fi

  artifact="$LOG_DIR/artifact_${wid}_$(basename "$sim" .py)_$(date +%s).log"
  run_sim_with_timeout "$sim" "$artifact"
  exit_code=$?
  if [ "$exit_code" -eq 124 ]; then
    echo "[$(date -Iseconds)] TIMEOUT after ${SIM_TIMEOUT}s: $sim" >> "$artifact"
    emit timeout "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"timeout_sec\":$SIM_TIMEOUT"
  fi
  sha=$(shasum -a 256 "$artifact" | awk '{print $1}')
  complete_args=(complete --claim-path "$claim_path" --exit "$exit_code" --artifact "$artifact")
  [ "$STRICT_RECEIPT_ADMISSION" = "1" ] && complete_args+=(--require-receipt)
  if ! complete_json=$("$PY" "$QUEUE_CLAIM" "${complete_args[@]}" 2>/dev/null); then
    emit complete_error "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"exit\":$exit_code,\"msg\":\"complete_failed\""
  else
    terminal_state=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1]).get('terminal_state',''))" "$complete_json" 2>/dev/null || echo "")
    blocked_reason=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1]).get('blocked_reason') or '')" "$complete_json" 2>/dev/null || echo "")
    if [ "$terminal_state" = "blocked" ]; then
      if [ "$blocked_reason" = "done_duplicate_conflict" ]; then
        emit duplicate "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"exit\":$exit_code,\"reason\":\"done_duplicate_conflict\""
      else
        emit gate_denied "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"exit\":$exit_code,\"reason\":\"${blocked_reason:-complete_blocked}\""
      fi
    else
      emit claimed "\"lane\":\"$lane\",\"worker\":\"$wid\",\"sim\":\"$sim\",\"exit\":$exit_code,\"artifact\":\"$artifact\",\"sha256\":\"$sha\""
    fi
  fi
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
import json, os, hashlib, sys
from pathlib import Path
root = Path(os.environ["ROOT"])
events = [json.loads(l) for l in Path(os.environ["EVENTS_PATH"]).read_text().splitlines() if l.strip()]
claimed = [e for e in events if e["kind"] == "claimed"]
duplicates = [e for e in events if e["kind"] == "duplicate"]
denied  = [e for e in events if e["kind"] == "gate_denied"]
Path(os.environ["MANIFEST_PATH"]).write_text(json.dumps(claimed + duplicates, indent=2))
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
dup_a = [e for e in duplicates if e.get("lane") == "A"]
dup_b = [e for e in duplicates if e.get("lane") == "B"]
summary = {
    "lane_a": {
        "claimed": len(lane_a),
        "duplicate": len(dup_a),
        "pass": sum(1 for e in lane_a if e["exit"] == 0),
        "fail": sum(1 for e in lane_a if e["exit"] != 0),
        "gate_denied": len(denied),
    },
    "lane_b": {
        "claimed": len(lane_b),
        "duplicate": len(dup_b),
        "pass": sum(1 for e in lane_b if e["exit"] == 0),
        "fail": sum(1 for e in lane_b if e["exit"] != 0),
    },
    "total_events": len(events),
}
if summary["total_events"] == 0:
    summary["status"] = "blocked_no_events"
    events.append(
        {
            "ts": "",
            "kind": "batch_complete",
            "reason": "no_events_claimed_or_reported",
            "lane_a_claims": summary["lane_a"]["claimed"],
            "lane_b_claims": summary["lane_b"]["claimed"],
            "wallclock": "no_movement",
        }
    )
else:
    summary["status"] = "complete"
Path(os.environ["SUCCESS_PATH"]).write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
sys.exit(0 if summary["status"] == "complete" else 1)
PY
}

# --- main -------------------------------------------------------------------
say "two-runner start minutes=$MINUTES K1=$K1 K2=$K2 dry=$DRY"

if ! helper_process_preflight; then
  say "FAILED helper process preflight; stop stale Computer Use helpers before non-browser parallel runner work."
  exit 1
fi

if ! admission_bypass_preflight; then
  say "FAILED admission bypass preflight; strict receipt and Wizard queue admission must stay enabled unless recovery sentinel exists."
  exit 1
fi

if ! acquire_lock; then
  say "FAILED to acquire $LOCK"
  exit 1
fi
record_lock_meta
trap cleanup EXIT
trap 'cleanup; exit 130' INT TERM

if [ "$DRY" -eq 1 ]; then
  if ! repair_duplicate_done_records; then
    exit 1
  fi
  echo "DRY: controller lock $LOCK held by $$"
  echo "DRY: spawn $K1 Lane A workers loop(claim lane_A -> gate -> run -> complete) until $MINUTES min"
  echo "DRY: spawn $K2 Lane B workers loop(claim lane_B -> run -> complete) until $MINUTES min"
  if [ "$K1" -gt 0 ]; then
    for i in $(seq 1 "$K1"); do worker_once "A" "$LANE_A_DIR" 1 "laneA_w${i}" || true; done
  fi
  if [ "$K2" -gt 0 ]; then
    for i in $(seq 1 "$K2"); do worker_once "B" "$LANE_B_DIR" 0 "laneB_w${i}" || true; done
  fi
  echo "DRY: wait for pools, then write reports:"
  echo "DRY:  $MANIFEST"
  echo "DRY:  $DENIALS"
  echo "DRY:  $TOOLSTATE"
  echo "DRY:  $SUCCESS"
  exit 0
fi

if ! repair_duplicate_done_records; then
  exit 1
fi

END_TS=$(( $(date +%s) + MINUTES * 60 ))
pids=()
if [ "$K1" -gt 0 ]; then
  for i in $(seq 1 "$K1"); do
    worker_loop "A" "$LANE_A_DIR" 1 "laneA_w${i}" "$END_TS" &
    pids+=("$!")
  done
fi
if [ "$K2" -gt 0 ]; then
  for i in $(seq 1 "$K2"); do
    worker_loop "B" "$LANE_B_DIR" 0 "laneB_w${i}" "$END_TS" &
    pids+=("$!")
  done
fi
say "spawned ${#pids[@]} workers; budget ends $(date -r "$END_TS" -Iseconds 2>/dev/null || date -Iseconds)"

# wait for budget, then graceful shutdown
while [ "$(date +%s)" -lt "$END_TS" ]; do sleep 30; done
say "budget expired; terminating pools"
stop_workers

if ! write_reports; then
  say "batch produced no events; stop by policy"
  exit 1
fi
say "reports written: $MANIFEST $DENIALS $TOOLSTATE $SUCCESS"
