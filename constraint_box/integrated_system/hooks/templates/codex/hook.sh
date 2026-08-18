#!/bin/sh
# Install-plan template: bind CB_HOOK_ROOT, CB_PRODUCT_ROOT, CB_LIGHT_PYTHON,
# and CB_HOOK_EVENT_LOG in the host environment before invoking this file.
set -eu
exec "${CB_HOOK_ROOT:?CB_HOOK_ROOT_REQUIRED}/cb_hook.sh" codex
