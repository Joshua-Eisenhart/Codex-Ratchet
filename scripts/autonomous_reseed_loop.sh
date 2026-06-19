#!/bin/bash
# Self-extending autonomous loop: re-seeds lane_A (canonical) and lane_B (classical)
# every CYCLE_SEC; exits after IDLE_CYCLES consecutive cycles with nothing to enqueue.
# No API calls, no tokens.
set -u
ROOT="${CODEX_RATCHET_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}"
PY="${CODEX_RATCHET_PYTHON:-${SIM_PY:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}}"
RESULTS="$ROOT/system_v4/probes/a2_state/sim_results"
RESEED_PIDFILE="/tmp/codex_ratchet_autonomous_reseed.pid"
cd "$ROOT"
CYCLE_SEC=${CYCLE_SEC:-300}   # 5 min
IDLE_CYCLES=${IDLE_CYCLES:-4} # exit after 20 min idle
MAX_HOURS=${MAX_HOURS:-8}
DEADLINE=$(( $(date +%s) + MAX_HOURS*3600 ))
LOG="$ROOT/overnight_logs/autonomous_reseed_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$ROOT/overnight_logs"

clear_reseed_pidfile() {
  if [ -f "$RESEED_PIDFILE" ] && [ "$(cat "$RESEED_PIDFILE" 2>/dev/null)" = "$$" ]; then
    rm -f "$RESEED_PIDFILE"
  fi
}

RUNNER_PID=""

cleanup_reseed() {
  if [ -n "$RUNNER_PID" ] && kill -0 "$RUNNER_PID" 2>/dev/null; then
    echo "[$(date)] stopping overnight runner pid=$RUNNER_PID" >> "$LOG"
    kill "$RUNNER_PID" 2>/dev/null || true
  fi
  clear_reseed_pidfile
}

acquire_reseed_pidfile() {
  for _ in 1 2; do
    if ( set -o noclobber; printf '%s\n' "$$" > "$RESEED_PIDFILE" ) 2>/dev/null; then
      trap cleanup_reseed EXIT
      trap 'trap - EXIT; cleanup_reseed; exit 130' INT TERM
      return 0
    fi
    existing=$(cat "$RESEED_PIDFILE" 2>/dev/null || true)
    if [ -n "$existing" ] && kill -0 "$existing" 2>/dev/null; then
      return 1
    fi
    rm -f "$RESEED_PIDFILE"
  done
  return 1
}

sim_running_under_pinned_python() {
  "$PY" - "$1" "$ROOT" "$PY" <<'PY'
import subprocess
import sys
from pathlib import Path

target = sys.argv[1]
root = Path(sys.argv[2])
py = sys.argv[3]
target_path = Path(target)
prefixes = {f"{py} {target}"}
try:
    if target_path.is_absolute():
        prefixes.add(f"{py} {target_path.relative_to(root)}")
    else:
        prefixes.add(f"{py} {root / target_path}")
except Exception:
    pass
try:
    proc = subprocess.run(["pgrep", "-af", py], capture_output=True, text=True, timeout=5)
except Exception:
    raise SystemExit(1)
if proc.returncode not in (0, 1):
    raise SystemExit(1)
for line in proc.stdout.splitlines():
    _, _, cmd = line.partition(" ")
    if any(cmd.startswith(prefix) for prefix in prefixes):
        raise SystemExit(0)
raise SystemExit(1)
PY
}

sim_family() {
  local base
  base=$(basename "$1" .py)
  base=${base#sim_}
  printf '%s\n' "${base%%_*}"
}

plan_bucket_for_sim() {
  case "$(sim_family "$1")" in
    axis|axis0|bridge|capability|clifford|cvc5|geom|geomstats|gerbe|gtower|gudhi|integration|lego|pure|pyg|qit|rustworkx|spectral|toponetx|torch|weyl|xgi|z3)
      echo "core_ladder"
      ;;
    fep|holodeck|iching|igt|leviathan)
      echo "framework_doctrine"
      ;;
    *)
      echo "exploratory"
      ;;
  esac
}

priority_for_bucket() {
  case "$1" in
    core_ladder) echo "high" ;;
    framework_doctrine) echo "low" ;;
    *) echo "normal" ;;
  esac
}

plan_stage_for_sim() {
  local base family
  base=$(basename "$1" .py)
  base=${base#sim_}
  family=${base%%_*}
  case "$base" in
    classical_baseline_*) echo "early_core"; return 0 ;;
  esac
  case "$family" in
    axis|axis0) echo "late_axis" ;;
    *)
      case "$base" in
        *bipartite*|*entanglement*|*mutual_information*|*mutual_info*|*coherent_information*|*coherent_info*|*concurrence*|*negativity*|*schmidt*|*entropy*|*capacity*|*capacities*|*carnot*|*szilard*|*landauer*|*thermo*)
          echo "late_info"
          ;;
        *)
          echo "early_core"
          ;;
      esac
      ;;
  esac
}

stage_gate_claim_for_sim() {
  local sim="$1" base family
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
  family=${base%%_*}
  case "$base" in
    classical_baseline_*) return 1 ;;
    *tier_d*|*boundary_flux*) echo "tier_d"; return 0 ;;
    *bridge*|*coupling*|*pairwise*|*coexistence*|*rho_ab*|*phi0*|*emergence*) echo "scientific_coupling"; return 0 ;;
  esac
  case "$family" in
    axis|axis0) echo "axis"; return 0 ;;
  esac
  case "$(plan_stage_for_sim "$sim")" in
    late_axis) echo "axis"; return 0 ;;
    late_info) echo "default_late_stage"; return 0 ;;
  esac
  return 1
}

stage_gate_allows_sim() {
  local sim="$1" claim
  claim=$(stage_gate_claim_for_sim "$sim") || return 0
  "$PY" scripts/stage_gate.py --claim "$claim" >/dev/null 2>&1
}

idle=0
if ! acquire_reseed_pidfile; then
  echo "[$(date)] existing reseed pidfile is alive; exiting duplicate" >> "$LOG"
  exit 0
fi

while :; do
  [ "$(date +%s)" -ge "$DEADLINE" ] && echo "[$(date)] deadline reached, exit" >> "$LOG" && exit 0

  # enqueue any sim (excluding " 2.py" copies and blacklisted meta-sims) missing a results file
  BLACKLIST_PATTERN="sim_timing_benchmark.py|autoresearch_sim_harness.py|exploratory_process_cycle_stage_matrix_sim.py|stage_matrix_neg_lib.py"
  enq=0
  for sim in system_v4/probes/sim_*.py; do
    [[ "$sim" == *" 2.py" ]] && continue
    echo "$(basename "$sim")" | grep -qE "^($BLACKLIST_PATTERN)$" && continue
    sim_abs="$ROOT/${sim#./}"
    base=$(basename "$sim" .py)
    rj="system_v4/probes/a2_state/sim_results/${base}_results.json"
    [ -f "$rj" ] && continue
    # skip if already queued/claimed
    if ls system_v4/probes/a2_state/queue/lane_A/*.json 2>/dev/null | xargs grep -l -e "\"$sim\"" -e "\"$sim_abs\"" >/dev/null 2>&1; then continue; fi
    if ls system_v4/probes/a2_state/queue/lane_B/*.json 2>/dev/null | xargs grep -l -e "\"$sim\"" -e "\"$sim_abs\"" >/dev/null 2>&1; then continue; fi
    if ls system_v4/probes/a2_state/queue/claimed/*.json* 2>/dev/null | xargs grep -l -e "\"$sim\"" -e "\"$sim_abs\"" >/dev/null 2>&1; then continue; fi
    # classify: canonical sims (check for classification = "canonical") go lane_A, rest lane_B
    lane="lane_B"
    grep -q '^classification\s*=\s*"canonical"' "$sim" 2>/dev/null && lane="lane_A"
    bucket=$(plan_bucket_for_sim "$sim")
    priority=$(priority_for_bucket "$bucket")
    stage=$(plan_stage_for_sim "$sim")
    if ! stage_gate_allows_sim "$sim"; then
      echo "[$(date)] stage gate blocked enqueue sim=$sim stage=$stage" >> "$LOG"
      continue
    fi
    "$PY" - "$ROOT" "$lane" "$sim_abs" "$priority" "$bucket" "$stage" <<'PY'
import hashlib
import json
import os
import sys
import time
from pathlib import Path

root, lane, sim_abs, priority, bucket, stage = sys.argv[1:]
queue_dir = Path(root) / "system_v4/probes/a2_state/queue" / lane
queue_dir.mkdir(parents=True, exist_ok=True)
digest = hashlib.sha1(f"{lane}:{sim_abs}".encode()).hexdigest()[:16]
target = queue_dir / f"{digest}.json"
payload = {
    "enqueued_at": int(time.time()),
    "lane": lane,
    "sim_path": sim_abs,
    "priority": priority,
    "plan_bucket": bucket,
    "plan_stage": stage,
}
try:
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
except FileExistsError:
    try:
        existing = json.loads(target.read_text())
    except Exception:
        existing = {}
    existing["sim_path"] = sim_abs
    existing["lane"] = lane
    existing["plan_bucket"] = bucket
    existing["plan_stage"] = stage
    existing["priority"] = priority
    existing["enqueued_at"] = existing.get("enqueued_at", payload["enqueued_at"])
    target.write_text(json.dumps(existing, sort_keys=True))
else:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
PY
    enq=$((enq+1))
  done

  # === free local maintenance (no tokens) ===
  # report duplicate copy-file count, but do not move active probe files from the loop
  copy_count=$(find system_v4/probes -maxdepth 1 -name "* 2.py" 2>/dev/null | wc -l)

  # release dead claims after a short grace window so a crashed pool does not freeze overnight
  now=$(date +%s)
  for cf in system_v4/probes/a2_state/queue/claimed/*.json.*; do
    [ -f "$cf" ] || continue
    mtime=$(stat -f %m "$cf" 2>/dev/null || echo "$now")
    age=$(( now - mtime ))
    [ "$age" -lt 300 ] && continue
    # Check liveness by sim_path, not the ephemeral claim subprocess PID.
    # parts[3] in the filename is the queue_claim.py subprocess PID — always dead.
    sim_path=$("$PY" -c "import json; print(json.load(open('$cf')).get('sim_path',''))" 2>/dev/null || echo "")
    if [ -n "$sim_path" ] && sim_running_under_pinned_python "$sim_path"; then
      continue  # sim still running — do not release
    fi
    # sim not running and claim is stale: release back to lane
    lane=$("$PY" -c "import json; print(json.load(open('$cf')).get('lane','lane_B'))" 2>/dev/null || echo lane_B)
    base=$(basename "$cf" | cut -d. -f1)
    echo "[$(date)] releasing stale claim: $(basename $cf) -> $lane" >> "$LOG"
    mv "$cf" "system_v4/probes/a2_state/queue/${lane}/${base}.json" 2>/dev/null
  done

  # auto-retag: sims declared classical_baseline but depth marks a nonclassical tool load_bearing → canonical candidate (flag only, don't silently promote)
  "$PY" -c "
import pathlib, re, json
flagged = []
for p in pathlib.Path('system_v4/probes').glob('sim_*.py'):
    if ' 2.py' in p.name: continue
    t = p.read_text()
    if re.search(r'^classification\s*=\s*\"classical_baseline\"', t, re.M):
        if re.search(r'\"(z3|cvc5|sympy|clifford|e3nn|geomstats|toponetx|gudhi|xgi|pyg)\"\s*:\s*\"load_bearing\"', t):
            flagged.append(str(p))
pathlib.Path('overnight_logs/retag_candidates.json').write_text(json.dumps(flagged, indent=2))
print(f'retag candidates flagged: {len(flagged)}')
" 2>&1

  # auto-commit result artifacts only; do not scoop unrelated source edits mid-run
  if [ -n "$(git status --porcelain system_v4/probes/a2_state/sim_results/ 2>/dev/null | head -1)" ]; then
    git add system_v4/probes/a2_state/sim_results/ 2>/dev/null
    if ! git diff --cached --quiet -- system_v4/probes/a2_state/sim_results/; then
      git commit --no-verify -m "auto: sim-results snapshot $(date +%Y%m%d_%H%M)" 2>&1 | tail -2
    fi
  fi

  # run audits every cycle (free — local only)
  {
    echo "=== AUDIT [$(date)] ==="
    "$PY" scripts/queue_claim.py 2>/dev/null
    echo "copy_candidates=$copy_count"
    "$PY" scripts/check_classification.py 2>/dev/null | "$PY" -c "import json,sys; d=json.loads(sys.stdin.read()); print(f\"classification: ok={d.get('ok',0)} missing={len(d.get('missing',[]))} invalid={len(d.get('invalid',[]))} parse_error={len(d.get('parse_errors',[]))} non_literal={len(d.get('non_literal',[]))}\")" 2>/dev/null
    "$PY" scripts/check_witnesses.py 2>/dev/null | "$PY" -c "import json,sys; d=json.loads(sys.stdin.read()); print(f\"witnesses: checked={d.get('checked',0)} violations={d.get('violation_count',0)}\")" 2>/dev/null
    "$PY" scripts/lint_sim_contract.py 2>/dev/null | "$PY" -c "import json,sys; d=json.loads(sys.stdin.read()); print(f\"contract: checked={d.get('checked',0)} sims_with_violations={d.get('sims_with_violations',0)} total={d.get('violation_total',0)} c6={d.get('violations_by_type',{}).get('C6_classical_has_load_bearing',0)}\")" 2>/dev/null
    # blocked audit: reasons histogram
    find system_v4/probes/a2_state/queue/blocked -type f -name '*.json*' 2>/dev/null | head -500 | xargs -I{} "$PY" -c "import json,sys; d=json.load(open('{}'));print(d.get('blocked_reason','?'))" 2>/dev/null | sort | uniq -c | sort -rn | head -5
    echo "done_recent_5min=$(find system_v4/probes/a2_state/queue/done -type f -mmin -5 2>/dev/null | wc -l)"
  } >> "$LOG" 2>&1

  echo "[$(date)] enqueued=$enq" >> "$LOG"
  if [ "$enq" -eq 0 ]; then
    idle=$((idle+1))
    echo "[$(date)] idle_cycles=$idle/$IDLE_CYCLES" >> "$LOG"
    if [ "$idle" -ge "$IDLE_CYCLES" ]; then
      echo "[$(date)] nothing left to do, exiting" >> "$LOG"
      exit 0
    fi
  else
    idle=0
  fi

  # clear a dead runner lock before trying to respawn
  if [ -f /tmp/codex_ratchet_overnight.lock ]; then
    lock_pid=$(cat /tmp/codex_ratchet_overnight.lock 2>/dev/null)
    if [ -n "$lock_pid" ] && ! kill -0 "$lock_pid" 2>/dev/null; then
      rm -f /tmp/codex_ratchet_overnight.lock
      echo "[$(date)] cleared stale runner lock pid=$lock_pid" >> "$LOG"
    fi
  fi

  # restart runner if no active lock holder remains
  if [ ! -f /tmp/codex_ratchet_overnight.lock ]; then
    mins=$(( (DEADLINE - $(date +%s)) / 60 ))
    if [ "$mins" -gt 10 ]; then
      if "$PY" scripts/stage_gate.py >/dev/null 2>&1; then
        nohup bash scripts/overnight_two_runner.sh --minutes "$mins" --lane-a-parallel 3 --lane-b-parallel 5 >> "$LOG" 2>&1 &
      else
        echo "[$(date)] stage gate unavailable; not respawning runner" >> "$LOG"
        sleep "$CYCLE_SEC"
        continue
      fi
      RUNNER_PID=$!
    fi
    echo "[$(date)] respawned runner for $mins min" >> "$LOG"
  fi

  sleep "$CYCLE_SEC"
done
