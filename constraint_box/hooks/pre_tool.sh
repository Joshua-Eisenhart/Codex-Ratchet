#!/bin/bash
set -eu
repo=$(cd "$(dirname "$0")/../.." && pwd)
exec bash "$repo/.claude/hooks/cb_pretooluse_guard.sh"
