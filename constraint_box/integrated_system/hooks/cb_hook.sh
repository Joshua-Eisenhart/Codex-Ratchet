#!/bin/sh
# Portable host-neutral hook entrypoint.
#
# The host supplies the product, capability, and event-log bindings.  The
# policing executable is fixed to the macOS system bootstrap; CB_LIGHT_PYTHON
# is data to attest, never the executable that decides whether it is valid.
# This shim never sets an import path override; ``-I`` keeps the route stdlib-
# only and source-bound.
set -eu

# Resolve the shim's own directory with shell primitives before selecting any
# interpreter.  A symlinked shim, relocated hook directory, or mismatched
# explicit product root is a custody hold, not a Python-level policy result.
shim_arg=$0
case "$shim_arg" in
  /*) shim_path=$shim_arg ;;
  *) shim_path=$(pwd -P)/$shim_arg ;;
esac
shim_parent=${shim_path%/*}
if [ "$shim_parent" = "$shim_path" ]; then
  shim_parent=.
fi
hooks_dir=$(CDPATH= cd -- "$shim_parent" && pwd -P) || {
  printf '%s\n' 'HOLD_HOOK_SHIM_DIRECTORY_UNRESOLVED' >&2
  exit 2
}
shim_name=${shim_path##*/}
shim_canon=$hooks_dir/$shim_name
if [ -L "$shim_canon" ]; then
  printf '%s\n' 'HOLD_HOOK_SHIM_SYMLINK' >&2
  exit 2
fi
if [ ! -f "$shim_canon" ]; then
  printf '%s\n' 'HOLD_HOOK_SHIM_NOT_REGULAR' >&2
  exit 2
fi
integrated_dir=${hooks_dir%/*}
shim_product_root=${integrated_dir%/*}
expected_hooks=$shim_product_root/integrated_system/hooks
expected_hooks_canon=$(CDPATH= cd -- "$expected_hooks" && pwd -P) || {
  printf '%s\n' 'HOLD_HOOK_PRODUCT_LAYOUT_UNRESOLVED' >&2
  exit 2
}
if [ "$expected_hooks_canon" != "$hooks_dir" ]; then
  printf '%s\n' 'HOLD_HOOK_PRODUCT_LAYOUT_MISMATCH' >&2
  exit 2
fi
hook_source=$hooks_dir/portable_host_hook.py
if [ -L "$hook_source" ]; then
  printf '%s\n' 'HOLD_HOOK_SOURCE_SYMLINK' >&2
  exit 2
fi
if [ ! -f "$hook_source" ]; then
  printf '%s\n' 'HOLD_HOOK_SOURCE_NOT_REGULAR' >&2
  exit 2
fi
hook_links=$(/usr/bin/stat -f '%l' "$hook_source") || {
  printf '%s\n' 'HOLD_HOOK_SOURCE_LINK_COUNT_UNREADABLE' >&2
  exit 2
}
case "$hook_links" in
  1) ;;
  *)
    printf '%s\n' 'HOLD_HOOK_SOURCE_MULTILINK' >&2
    exit 2
    ;;
esac
hook_source_dir=$(CDPATH= cd -- "${hook_source%/*}" && pwd -P) || {
  printf '%s\n' 'HOLD_HOOK_SOURCE_DIRECTORY_UNRESOLVED' >&2
  exit 2
}
hook_source_canon=$hook_source_dir/${hook_source##*/}
case "$hook_source_canon" in
  "$shim_product_root"/*) ;;
  *)
    printf '%s\n' 'HOLD_HOOK_SOURCE_OUTSIDE_SHIM_PRODUCT' >&2
    exit 2
    ;;
esac
host=${1:-}
product_root=${CB_PRODUCT_ROOT:-}
light_python=${CB_LIGHT_PYTHON:-${CB_LIGHT_INTERPRETER:-}}
event_log=""
bootstrap_python=/usr/bin/python3

case "$host" in
  codex|claude|grok|hermes) ;;
  *)
    printf '%s\n' 'HOLD_HOST_NAME_REQUIRED' >&2
    exit 2
    ;;
esac
if [ -z "$product_root" ]; then
  printf '%s\n' 'HOLD_CB_PRODUCT_ROOT_REQUIRED' >&2
  exit 2
fi
if [ ! -d "$product_root" ]; then
  printf 'HOLD_CB_PRODUCT_ROOT_MISSING:%s\n' "$product_root" >&2
  exit 2
fi
product_root_canon=$(CDPATH= cd -- "$product_root" && pwd -P) || {
  printf '%s\n' 'HOLD_CB_PRODUCT_ROOT_UNRESOLVED' >&2
  exit 2
}
if [ "$product_root_canon" != "$shim_product_root" ]; then
  printf '%s\n' 'HOLD_HOOK_SHIM_PRODUCT_ROOT_MISMATCH' >&2
  exit 2
fi
product_root=$shim_product_root
CB_PRODUCT_ROOT=$product_root
export CB_PRODUCT_ROOT
if [ ! -x "$bootstrap_python" ]; then
  printf 'HOLD_CB_HOOK_BOOTSTRAP_INTERPRETER_MISSING:%s\n' "$bootstrap_python" >&2
  exit 2
fi
event_log=$product_root/integrated_system/runs/hook-events.jsonl

exec "$bootstrap_python" -I "$hook_source" \
  --host "$host" \
  --product-root "$product_root" \
  --light-interpreter "$light_python" \
  --event-log "$event_log" \
  --hook-source "$hook_source_canon"
