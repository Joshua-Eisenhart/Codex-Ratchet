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

# The Light gate ignores non-mutations. After a package mutation it re-observes
# the actual interpreter, executes the five bounded tool contracts, runs SMT
# selection across the full proposal domain, and commits the rows to SQLite.
output=$("$python" -I -m hookkernel.cb_light_gate \
  post-tool --payload-json "$input" 2>&1)
status=$?
if [[ $status -ne 0 ]]; then
  printf '%s\n' "$output" >&2
  exit 2
fi

exit 0
