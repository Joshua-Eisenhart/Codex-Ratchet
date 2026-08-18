#!/bin/bash
set -u
hook_dir=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$hook_dir/../.." && pwd)
interpreter="$repo/constraint_box/.venv/bin/python"
if [ ! -x "$interpreter" ]; then
  echo "CB Light contained interpreter missing: $interpreter" >&2
  exit 2
fi
"$interpreter" -B -I "$hook_dir/cb_light_hook.py" post-tool-batch
code=$?
if [ "$code" -eq 0 ] || [ "$code" -eq 2 ]; then exit "$code"; fi
echo "CB Light hook execution failed closed: rc=$code" >&2
exit 2
