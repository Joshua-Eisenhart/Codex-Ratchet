#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
light_python=${CB_LIGHT_PYTHON:-}
if [ -z "$light_python" ] || [ ! -x "$light_python" ]; then
  printf '%s\n' 'HOLD_CB_LIGHT_INTERPRETER_REQUIRED' >&2
  exit 2
fi
host=${1:-}
if [ -n "$host" ]; then
  exec "$light_python" "$here/bin/cb" --light-python "$light_python" hook "$host"
fi
exec "$light_python" "$here/bin/cb" --light-python "$light_python" hook
