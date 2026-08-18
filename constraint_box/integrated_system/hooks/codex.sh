#!/bin/sh
set -eu
exec "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/cb_hook.sh" codex
