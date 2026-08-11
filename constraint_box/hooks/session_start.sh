#!/bin/bash
set -eu
repo=$(cd "$(dirname "$0")/../.." && pwd)
exec bash "$repo/.claude/hooks/session-start.sh"
