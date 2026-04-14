#!/bin/bash
# Self-extending autonomous loop: re-seeds lane_A (canonical) and lane_B (classical)
# every CYCLE_SEC; exits after IDLE_CYCLES consecutive cycles with nothing to enqueue.
# No API calls, no tokens.
set -u
ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
cd "$ROOT"
CYCLE_SEC=${CYCLE_SEC:-300}   # 5 min
IDLE_CYCLES=${IDLE_CYCLES:-4} # exit after 20 min idle
MAX_HOURS=${MAX_HOURS:-8}
DEADLINE=$(( $(date +%s) + MAX_HOURS*3600 ))
LOG="$ROOT/overnight_logs/autonomous_reseed_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$ROOT/overnight_logs"

idle=0
while :; do
  [ "$(date +%s)" -ge "$DEADLINE" ] && echo "[$(date)] deadline reached, exit" >> "$LOG" && exit 0

  # enqueue any sim (excluding " 2.py" copies) missing a results file
  enq=0
  for sim in system_v4/probes/sim_*.py; do
    [[ "$sim" == *" 2.py" ]] && continue
    base=$(basename "$sim" .py)
    rj="system_v4/probes/a2_state/sim_results/${base}_results.json"
    [ -f "$rj" ] && continue
    # skip if already queued/claimed
    if ls system_v4/probes/a2_state/queue/lane_A/*.json 2>/dev/null | xargs grep -l "\"$sim\"" >/dev/null 2>&1; then continue; fi
    if ls system_v4/probes/a2_state/queue/lane_B/*.json 2>/dev/null | xargs grep -l "\"$sim\"" >/dev/null 2>&1; then continue; fi
    if ls system_v4/probes/a2_state/queue/claimed/*.json* 2>/dev/null | xargs grep -l "\"$sim\"" >/dev/null 2>&1; then continue; fi
    # classify: canonical sims (check for classification = "canonical") go lane_A, rest lane_B
    lane="lane_B"
    grep -q '^classification\s*=\s*"canonical"' "$sim" 2>/dev/null && lane="lane_A"
    ID=$(python3 -c "import secrets; print(secrets.token_hex(8))")
    printf '{"enqueued_at": %s, "lane": "%s", "sim_path": "%s"}\n' "$(date +%s)" "$lane" "$sim" > "system_v4/probes/a2_state/queue/${lane}/${ID}.json"
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
    pid=$(basename "$cf" | awk -F. '{print $3}')
    kill -0 "$pid" 2>/dev/null && continue
    # pid dead, claim stale: move back to lane
    lane=$(python3 -c "import json; print(json.load(open('$cf')).get('lane','lane_B'))" 2>/dev/null || echo lane_B)
    base=$(basename "$cf" | cut -d. -f1)
    mv "$cf" "system_v4/probes/a2_state/queue/${lane}/${base}.json" 2>/dev/null
  done

  # auto-retag: sims declared classical_baseline but depth marks a nonclassical tool load_bearing → canonical candidate (flag only, don't silently promote)
  python3 -c "
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
    python3 scripts/queue_claim.py 2>/dev/null
    echo "copy_candidates=$copy_count"
    python3 scripts/check_classification.py 2>/dev/null | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(f\"classification: ok={d.get('ok',0)} missing={len(d.get('missing',[]))} invalid={len(d.get('invalid',[]))} parse_error={len(d.get('parse_errors',[]))} non_literal={len(d.get('non_literal',[]))}\")" 2>/dev/null
    python3 scripts/check_witnesses.py 2>/dev/null | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(f\"witnesses: checked={d.get('checked',0)} violations={d.get('violation_count',0)}\")" 2>/dev/null
    python3 scripts/lint_sim_contract.py 2>/dev/null | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(f\"contract: checked={d.get('checked',0)} sims_with_violations={d.get('sims_with_violations',0)} total={d.get('violation_total',0)} c6={d.get('violations_by_type',{}).get('C6_classical_has_load_bearing',0)}\")" 2>/dev/null
    # blocked audit: reasons histogram
    find system_v4/probes/a2_state/queue/blocked -type f -name '*.json*' 2>/dev/null | head -500 | xargs -I{} python3 -c "import json,sys; d=json.load(open('{}'));print(d.get('blocked_reason','?'))" 2>/dev/null | sort | uniq -c | sort -rn | head -5
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
    [ "$mins" -gt 10 ] && nohup bash scripts/overnight_two_runner.sh --minutes "$mins" --lane-a-parallel 3 --lane-b-parallel 5 >> "$LOG" 2>&1 &
    echo "[$(date)] respawned runner for $mins min" >> "$LOG"
  fi

  sleep "$CYCLE_SEC"
done
