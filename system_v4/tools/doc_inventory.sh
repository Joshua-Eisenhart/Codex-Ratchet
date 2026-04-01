#!/usr/bin/env bash
set -euo pipefail

DOC_DIR="$(cd "$(dirname "$0")/../docs" && pwd)"
MODE="${1:-all}"

ACTIVE_COUNT=0
SUPERSEDED_COUNT=0
UNMARKED_COUNT=0
ACTIVE_DOCS=()
SUP_DOCS=()
UNMARKED_DOCS=()

for file in "$DOC_DIR"/*.md; do
  base="$(basename "$file")"
  status="$(awk '/^\*\*Status:\*\*/ {gsub("^\\*\\*Status:\\*\\* ?", "", $0); print tolower($0); exit}' "$file" || true)"
  if [[ -n "$status" ]]; then
    if [[ "$status" == *superseded* || "$status" == *deprecated* ]]; then
      SUP_DOCS+=("$base")
      ((SUPERSEDED_COUNT++))
      continue
    fi
    ACTIVE_DOCS+=("$base")
    ((ACTIVE_COUNT++))
  else
    UNMARKED_DOCS+=("$base")
    ((UNMARKED_COUNT++))
  fi
done

emit_list() {
  local label="$1"
  shift
  local items=("$@")
  printf "%s (%s)\n" "$label" "${#items[@]}"
  for item in "${items[@]}"; do
    printf "  - %s\n" "$item"
  done
}

case "$MODE" in
  --active)
    emit_list "ACTIVE" "${ACTIVE_DOCS[@]}"
    ;;
  --superseded)
    emit_list "SUPERSEDED" "${SUP_DOCS[@]}"
    ;;
  --unmarked)
    emit_list "UNMARKED" "${UNMARKED_DOCS[@]}"
    ;;
  --all|*)
    echo "DOC INVENTORY ($DOC_DIR)"
    echo "ACTIVE:  $ACTIVE_COUNT"
    echo "SUPERSEDED: $SUPERSEDED_COUNT"
    echo "UNMARKED: $UNMARKED_COUNT"
    echo
    emit_list "ACTIVE" "${ACTIVE_DOCS[@]}"
    echo
    emit_list "SUPERSEDED" "${SUP_DOCS[@]}"
    echo
    emit_list "UNMARKED" "${UNMARKED_DOCS[@]}"
    ;;
esac
