#!/bin/bash
# Fired-side ClaimGate — the un-forgettability fix.
#
# ClaimGate's threat model, move #3: an LLM can SKIP a gate it must CALL, but it
# cannot skip a gate the HARNESS FIRES. This hook makes git the harness: every
# staged ratchet receipt is gated at commit time, so the gate can no longer be
# forgotten (it was, on 2026-07-22 — that forgetting is the finding this closes).
#
# Verdict mapping (claimgate_plugin/hooks/post_receipt_gate.sh exit codes):
#   0  VERIFIED / pass                       -> allow the file
#   3  INSUFFICIENT_DEPTH (admitted, not a   -> allow the file (honest probe depth)
#      rejection; deeper audit still owed)
#   1  REJECTED                              -> BLOCK the commit, print the fix
#   other (tooling/IO error)                 -> WARN, do not brick the commit
#
# Best-effort by design: a missing gate or a broken tool never bricks commits;
# it only ever BLOCKS on an explicit REJECTED (exit 1) verdict.
# NOTE: portable to bash 3.2 (macOS default) — no mapfile, no `set -u` array traps.
set -o pipefail

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
gate="$repo/claimgate_plugin/hooks/post_receipt_gate.sh"
if [[ ! -f "$gate" ]]; then
  echo "[claimgate pre-commit] gate script missing ($gate); skipping — not bricking commit." >&2
  exit 0
fi

blocked=0
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

# staged, added/copied/modified ratchet-receipt JSONs. Process substitution keeps
# the loop (and the `blocked` flag) in the main shell — a piped while would not.
while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  abs="$repo/$rel"
  [[ -f "$abs" ]] || continue
  # only gate files that are actually ratchet receipts (carry a verdict/classification)
  python3 -c "import json,sys
try:
    d=json.load(open('$abs'))
except Exception:
    sys.exit(1)
sys.exit(0 if ('verdict' in d or 'classification' in d) else 1)" 2>/dev/null || continue

  bash "$gate" "$abs" >"$tmp" 2>&1; rc=$?
  case "$rc" in
    0) echo "  [claimgate] pass (exit 0): $rel" >&2 ;;
    3) echo "  [claimgate] admitted, depth-pending (exit 3, not a rejection): $rel" >&2 ;;
    1) echo "⛔ [claimgate] REJECTED (exit 1): $rel — commit blocked." >&2
       sed -n '1,25p' "$tmp" >&2
       blocked=1 ;;
    *) echo "  [claimgate] tool error (exit $rc) on $rel — not blocking on tooling error." >&2 ;;
  esac
done < <(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '(ratchet_contract|system_v8|fuel_gate)/.*/results/.*\.json$' || true)

if [[ $blocked -eq 1 ]]; then
  echo "" >&2
  echo "Fix the rejected receipt(s), or run:  node claimgate_plugin/suggest.mjs <receipt.json>" >&2
  echo "for the paste-ready fix, then re-commit. (This gate is fired, not called — it cannot be skipped.)" >&2
  exit 1
fi
exit 0
