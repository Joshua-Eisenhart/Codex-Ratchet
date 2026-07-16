#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
QICS_CHECKOUT=/Users/joshuaeisenhart/GitHub/qics

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$QICS_CHECKOUT"
export NUMBA_CACHE_DIR=/tmp/codex_ratchet_qics_numba_cache

"$PYTHON" -B "$HERE/qics_battery.py" --self-test

FIRST=$("$PYTHON" -B "$HERE/qics_battery.py" --output "$HERE/result.json")
"$PYTHON" -B "$HERE/qics_battery.py" --validate "$FIRST"

SECOND=$("$PYTHON" -B "$HERE/qics_battery.py" --output "$HERE/rerun_result.json")
"$PYTHON" -B "$HERE/qics_battery.py" --validate "$SECOND"
"$PYTHON" -B "$HERE/qics_battery.py" --compare "$FIRST" "$SECOND"

/usr/bin/shasum -a 256 "$FIRST" "$SECOND"
printf '%s\n' "deterministic_rerun: PASS"
printf '%s\n' "first_result: $FIRST"
printf '%s\n' "second_result: $SECOND"
"$PYTHON" -B "$HERE/qics_battery.py" --summary "$FIRST"

# Required persistence witness: the base result remains present and untouched.
/bin/ls -la "$HERE/result.json"
