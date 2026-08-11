#!/bin/bash
set -u
input=$(cat)
repo=$(cd "$(dirname "$0")/../.." && pwd)
python="$repo/constraint_box/.venv/bin/python"
if [[ ! -x "$python" ]]; then
  printf 'CB Light contained interpreter missing: %s\n' "$python" >&2
  exit 2
fi
cd "$repo/constraint_box" || exit 2

# Every Bash command reaches the Python parser. Inspection commands return
# NOT_A_PACKAGE_MUTATION without output; package mutations are checked against
# the Light proposal domain, current direct roots, and the exact interpreter.
output=$("$python" -I -m hookkernel.cb_light_gate \
  pre-install --payload-json "$input" 2>&1)
status=$?
if [[ $status -ne 0 ]]; then
  printf '%s\n' "$output" >&2
  exit 2
fi
exit 0
