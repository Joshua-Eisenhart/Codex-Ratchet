#!/bin/sh
# Compatibility front door. The contained integrated shim is authoritative.
set -eu
host="${1:-}"
here=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
shim="$here/integrated_system/hooks/cb_hook.sh"
if [ ! -x "$shim" ]; then
  printf '%s\n' 'HOLD_CONTAINED_HOOK_SHIM_MISSING' >&2
  exit 2
fi

# This compatibility entrypoint owns the binding.  A caller may inherit a
# product-root variable from another checkout, but that value must never pick
# which contained hook this front door runs against.
CB_PRODUCT_ROOT="$here"
export CB_PRODUCT_ROOT

# The integrated hook records only the canonical ignored runtime log.  Ambient
# legacy/current log variables never select a source-tree or external path.
event_log="$here/integrated_system/runs/hook-events.jsonl"
CB_HOOK_EVENT_LOG="$event_log"
export CB_HOOK_EVENT_LOG

if [ -z "${CB_LIGHT_PYTHON:-}" ] && [ -x "$here/.venv/bin/python" ]; then
  CB_LIGHT_PYTHON="$here/.venv/bin/python"
  export CB_LIGHT_PYTHON
fi
if [ -n "$host" ]; then
  exec "$shim" "$host"
fi
exec "$shim"
