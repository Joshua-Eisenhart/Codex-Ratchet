#!/bin/sh
# Compatibility front door. The contained integrated shim is authoritative.
set -eu
host="${1:-}"
here=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
shim="$here/integrated_system/hooks/cb_hook.sh"
if [ ! -x "$shim" ]; then
  printf '%s\n' 'HOLD_CONTAINED_HOOK_SHIM_MISSING' >&2
  exit 2
fi
if [ -z "${CB_LIGHT_PYTHON:-}" ] && [ -x "$here/.venv/bin/python" ]; then
  CB_LIGHT_PYTHON="$here/.venv/bin/python"
  export CB_LIGHT_PYTHON
fi
if [ -n "$host" ]; then
  exec "$shim" "$host"
fi
exec "$shim"
