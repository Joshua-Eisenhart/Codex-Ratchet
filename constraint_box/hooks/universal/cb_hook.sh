#!/usr/bin/env bash
# Universal CB hook front door. Host is $1 (hermes|claude|codex|grok) or auto.
set -eu
host="${1:-}"
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
py="$root/.venv/bin/python"
export PYTHONNOUSERSITE=1
if [[ ! -x "$py" ]]; then
  py="${CB_HOOK_PYTHON:-python3}"
fi
cd "$root" || exit 2
# Do not use python -I: it drops PYTHONPATH and cannot import the current
# source package.  Module execution preserves package-relative imports used by
# the typed quarantine route; executing hook_adapter.py as a file does not.
export PYTHONPATH="$root/src${PYTHONPATH:+:$PYTHONPATH}"
if [[ -n "$host" ]]; then
  exec "$py" -m constraintbox.hook_adapter "$host"
else
  exec "$py" -m constraintbox.hook_adapter
fi
