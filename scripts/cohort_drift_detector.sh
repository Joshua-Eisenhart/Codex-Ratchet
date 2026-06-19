#!/usr/bin/env bash
# cohort_drift_detector.sh — V0 scout (Wave 8 / candidate W2)
#
# Scans configured paths for stale-cohort version strings and applies the R6
# classification heuristic from V3_4_CUTOVER_R6_CLASSIFICATION.md:
#   L — live-pointer on a boot surface (must bump)        → DRIFT (exit !=0)
#   V — versioned-cohort artifact (filename _vX_Y.md)     → ok, retain
#   N — negative-directive ("do not stage / flip")         → ok, but flag review
#   P — predecessor / source-hierarchy reference          → ok, retain
#
# Usage:
#   cohort_drift_detector.sh                       # default: stale = v3-3 / v3_3 / v3.3
#   COHORT_STALE='v3-4|v3_4|v3\.4' cohort_drift_detector.sh   # next cutover
#   PATHS_OVERRIDE="$HOME/wiki/wizard" cohort_drift_detector.sh

set -uo pipefail

# --- config -----------------------------------------------------------------
STALE_REGEX="${COHORT_STALE:-v3-3|v3_3|v3\.3}"

# Consumer boot surfaces only — this detector is scoped to the cohort cutover
# decision surface, not the whole research tree. To widen, set PATHS_OVERRIDE.
REPO_ROOT="${CODEX_RATCHET_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}"
DEFAULT_PATHS=(
  "$HOME/wiki/wizard"
  "$HOME/wiki/harness/README.md"
  "$REPO_ROOT/AGENTS.md"
  "$REPO_ROOT/CLAUDE.md"
  "$REPO_ROOT/system_v5/ops"
  "$REPO_ROOT/system_v5/docs/plans"
  "$HOME/.codex"
  "$HOME/.hermes"
)
if [[ -n "${PATHS_OVERRIDE:-}" ]]; then
  read -r -a SCAN_PATHS <<< "$PATHS_OVERRIDE"
else
  SCAN_PATHS=("${DEFAULT_PATHS[@]}")
fi

# Boot-surface filename allowlist — anchors the L heuristic.
BOOT_SURFACE_REGEX='(README|README_FIRST|AGENTS|CLAUDE|01-wizard-general|02-mmm-reference|03-followups|WIKI_STEWARD)\.md$|^.*/wizard/[0-9]+-.*\.md$'

# Skip noise.
EXCLUDE_REGEX='/(\.git|node_modules|__pycache__|\.venv|archive|archive_old|dist|build)/'

# --- scan -------------------------------------------------------------------
declare -a HITS_L HITS_V HITS_N HITS_P HITS_U
total=0

scan_one() {
  local root="$1"
  [[ -e "$root" ]] || return 0
  # Use grep to find version-string hits in text-ish files.
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    total=$((total+1))
    local file lineno content lc
    file="${line%%:*}"; rest="${line#*:}"
    lineno="${rest%%:*}"; content="${rest#*:}"
    lc="$(echo "$content" | tr '[:upper:]' '[:lower:]')"

    # Classify (order matters — first match wins).
    if [[ "$file" =~ _v3_3\.md$ ]] || [[ "$file" =~ _v3-3/ ]] || [[ "$file" =~ MMM_WIZARD_CLEAN_SYSTEM_PACKET_v3_3 ]]; then
      HITS_V+=("$file:$lineno: $content")
    elif [[ "$lc" == *"do not stage"* ]] || [[ "$lc" == *"do not flip"* ]] || [[ "$lc" == *"never flip"* ]]; then
      HITS_N+=("$file:$lineno: $content")
    elif [[ "$lc" == *"predecessor"* ]] || [[ "$lc" == *"what changed from"* ]] || [[ "$lc" == *"source-hierarchy"* ]] || [[ "$lc" == *"reference only"* ]] || [[ "$lc" == *"retirement"* ]]; then
      HITS_P+=("$file:$lineno: $content")
    elif [[ "$file" =~ $BOOT_SURFACE_REGEX ]]; then
      HITS_L+=("$file:$lineno: $content")
    else
      HITS_U+=("$file:$lineno: $content")
    fi
  done < <(grep -RInE "$STALE_REGEX" "$root" 2>/dev/null \
            | grep -vE "$EXCLUDE_REGEX" \
            | grep -vE '\.(zip|sha256|png|jpg|jpeg|gif|pdf|pyc|so|pkl)(:|$)')
}

for p in "${SCAN_PATHS[@]}"; do scan_one "$p"; done

# --- report -----------------------------------------------------------------
echo "=== cohort_drift_detector V0 ==="
echo "stale regex     : $STALE_REGEX"
echo "scanned paths   : ${SCAN_PATHS[*]}"
echo "total raw hits  : $total"
echo
print_class() {
  local name="$1"; shift
  local -a arr=("$@")
  echo "--- $name (${#arr[@]}) ---"
  for h in "${arr[@]}"; do echo "  $h"; done
  echo
}
print_class "L (live-pointer / boot surface — DRIFT)" "${HITS_L[@]:-}"
print_class "V (versioned-cohort artifact — retain)"  "${HITS_V[@]:-}"
print_class "N (negative-directive — review only)"     "${HITS_N[@]:-}"
print_class "P (predecessor / provenance — retain)"    "${HITS_P[@]:-}"
print_class "U (unclassified — human review)"          "${HITS_U[@]:-}"

l_count=${#HITS_L[@]}
u_count=${#HITS_U[@]}
echo "=== summary ==="
echo "L=$l_count  V=${#HITS_V[@]}  N=${#HITS_N[@]}  P=${#HITS_P[@]}  U=$u_count"

if (( l_count > 0 )) || (( u_count > 0 )); then
  echo "DRIFT DETECTED: L=$l_count, U=$u_count" >&2
  exit 2
fi
echo "no drift on active boot surfaces"
exit 0
