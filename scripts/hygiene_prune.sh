#!/bin/bash
# Hygiene: prune legacy, compress old results, keep working set lean.
# Local, zero tokens. Safe to run alongside perpetual_runner.
set -u
ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
cd "$ROOT"
LOG="$ROOT/overnight_logs/hygiene_$(date +%Y%m%d_%H%M%S).log"
exec >> "$LOG" 2>&1
echo "[$(date)] hygiene start"

# 1. Compress overnight_logs older than 1 day (skip already-gz)
find overnight_logs -type f -name "*.log" -mtime +1 ! -name "*.gz" -exec gzip -9 {} \;

# 2. Prune overnight_logs older than 14 days (gz or not)
find overnight_logs -type f -mtime +14 -delete

# 3. Compress sim result JSONs older than 7 days into per-week tarballs
ARCHIVE_DIR="system_v4/probes/a2_state/sim_results_archive"
mkdir -p "$ARCHIVE_DIR"
WEEK_TAG=$(date -v-7d +%Y%W 2>/dev/null || date -d "7 days ago" +%Y%W)
TARBALL="$ARCHIVE_DIR/results_week_${WEEK_TAG}.tar.gz"
OLD=$(find system_v4/probes/a2_state/sim_results -type f -name "*.json" -mtime +7)
if [ -n "$OLD" ]; then
  echo "$OLD" | tar -czf "$TARBALL" -T - 2>/dev/null && echo "$OLD" | xargs rm -f
  echo "archived $(echo "$OLD" | wc -l) result JSONs into $TARBALL"
fi

# 4. Prune .DS_Store droppings
find . -name ".DS_Store" -not -path "./.git/*" -delete

# 5. Health: kill stale runners >12h old (zombie protection)
ps -o pid,etimes,command -ax | awk '/overnight_two_runner.sh/ && $2 > 43200 {print $1}' | xargs -r kill 2>/dev/null

# 6. Disk report
echo "--- sizes ---"
du -sh overnight_logs system_v4/probes/a2_state/sim_results "$ARCHIVE_DIR" 2>/dev/null
echo "[$(date)] hygiene done"
