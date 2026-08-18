#!/bin/sh
set -eu
exec "${CB_HOOK_ROOT:?CB_HOOK_ROOT_REQUIRED}/cb_hook.sh" claude
