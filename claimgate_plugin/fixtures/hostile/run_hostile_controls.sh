#!/bin/bash
# run_hostile_controls.sh — ClaimGate hostile-control corpus regression runner.
#
# Standing regression for every future gate change. For each
# *.expected.json in this directory it re-runs the recorded gate_cmd and
# compares the fresh exit code to the RECORDED actual_exit (drift check).
# HOLDS/GAP is the recorded verdict from the fixture's expected.json; this
# runner never re-judges it — it only detects drift from the recorded
# actuals. If a gate change flips a recorded actual, that is DRIFT and the
# fixture's expected.json must be consciously re-baselined (honestly:
# GAP->HOLDS if the gate was hardened, HOLDS->GAP if it regressed).
#
# Output: one line per class:
#   class | expected_exit | actual_exit | HOLDS/GAP | drift?
# where actual_exit is the FRESH exit from this run.
#
# Exit: 0 = no drift from recorded actuals; 1 = at least one class drifted
#       (or an expected.json was unreadable).
#
# Placeholder convention: a gate_cmd containing the literal token
# <fixture> is expanded once per fixture. If the expected.json carries a
# per_fixture array with full_chain_exit values, each expansion is
# compared against its own recorded full_chain_exit and the printed
# actual_exit is the final expansion's fresh exit (matching the recorded
# top-level actual_exit, which by convention is the decisive/final
# fixture). Otherwise every expansion is compared to the top-level
# actual_exit.
#
# bash 3.2-portable: no mapfile/readarray, no associative arrays.
#
# classification: hostile_control_fixture (runner); promotion_allowed: false.
# This script only READS the gates; it never modifies gate, hook, or
# registry files.

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd) || exit 2

PY=python3
command -v python3 >/dev/null 2>&1 || PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3

# Python helper: prints a run plan for one expected.json.
#   line 1: class<TAB>expected_exit<TAB>recorded_actual_exit<TAB>status
#   lines 2..N: command<TAB>recorded_exit_for_that_command
# (No single-quote characters below — the string is single-quoted in bash.)
HELPER='
import json, sys
d = json.load(open(sys.argv[1]))
cmd = d.get("gate_cmd") or ""
cls = d.get("class") or "?"
exp = d.get("expected_exit")
act = d.get("actual_exit")
st = d.get("status") or "?"
runs = []
if "<fixture>" in cmd:
    pf = d.get("per_fixture") or []
    if pf and all(isinstance(x, dict) and "fixture" in x and "full_chain_exit" in x for x in pf):
        for x in pf:
            runs.append((cmd.replace("<fixture>", x["fixture"]), x["full_chain_exit"]))
    else:
        for fx in d.get("fixtures") or []:
            runs.append((cmd.replace("<fixture>", fx), act))
if not runs:
    runs.append((cmd, act))
sys.stdout.write("%s\t%s\t%s\t%s\n" % (cls, exp, act, st))
for c, a in runs:
    sys.stdout.write("%s\t%s\n" % (c, a))
'

TAB=$(printf '\t')
plan=$(mktemp "${TMPDIR:-/tmp}/hostile_plan.XXXXXX") || exit 2
runsfile=$(mktemp "${TMPDIR:-/tmp}/hostile_runs.XXXXXX") || exit 2
trap 'rm -f "$plan" "$runsfile"' EXIT

drift_any=0
found_any=0

echo "class | expected_exit | actual_exit | status | drift?"

for f in "$SCRIPT_DIR"/*.expected.json; do
  [ -e "$f" ] || continue
  found_any=1

  if ! "$PY" -c "$HELPER" "$f" > "$plan" 2>/dev/null || [ ! -s "$plan" ]; then
    echo "$(basename "$f" .expected.json) | ? | ? | UNREADABLE | DRIFT (expected.json unparseable)"
    drift_any=1
    continue
  fi

  header=$(head -n 1 "$plan")
  old_ifs=$IFS
  IFS=$TAB
  set -- $header
  IFS=$old_ifs
  cls=${1-?}; exp=${2-?}; rec=${3-?}; status=${4-?}

  tail -n +2 "$plan" > "$runsfile"

  class_drift=no
  fresh_last="?"
  drift_detail=""

  while IFS=$TAB read -r sub_cmd sub_rec; do
    [ -n "$sub_cmd" ] || continue
    ( cd "$REPO_ROOT" && eval "$sub_cmd" ) >/dev/null 2>&1 </dev/null
    rc=$?
    fresh_last=$rc
    if [ "$rc" != "$sub_rec" ]; then
      class_drift=yes
      drift_detail="recorded=$sub_rec fresh=$rc"
    fi
  done < "$runsfile"

  if [ "$class_drift" = "yes" ]; then
    drift_any=1
    echo "$cls | $exp | $fresh_last | $status | DRIFT ($drift_detail)"
  else
    echo "$cls | $exp | $fresh_last | $status | no-drift"
  fi
done

if [ "$found_any" -eq 0 ]; then
  echo "run_hostile_controls: no *.expected.json found in $SCRIPT_DIR" >&2
  exit 1
fi

if [ "$drift_any" -ne 0 ]; then
  echo "RESULT: DRIFT — at least one gate exit differs from its recorded actual_exit. Re-baseline consciously."
  exit 1
fi
echo "RESULT: no drift — all gate exits match recorded actuals."
exit 0
