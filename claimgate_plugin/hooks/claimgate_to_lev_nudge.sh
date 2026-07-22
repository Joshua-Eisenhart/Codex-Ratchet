#!/bin/bash
# ClaimGate -> Lev nudge emitter — the Lev-native enforcement twin of
# hooks/pre_commit_gate_receipts.sh (CR's git-fired leg). Where the git hook
# blocks a COMMIT on a REJECTED receipt, this script surfaces the SAME
# verdict on Lev's own orchestrator-to-orchestrator signal surface
# (.lev/nudges/), independent of whether the receipt is ever committed to
# CR's git at all.
#
# Verdict mapping (post_receipt_gate.sh exit codes -> nudge priority):
#   0  VERIFIED / pass          -> no nudge (nothing to report)
#   1  REJECTED                 -> priority 1 nudge (claim rejected, blocking)
#   3  INSUFFICIENT_DEPTH       -> priority 3 nudge (admitted, deeper audit owed)
#   other (tooling/IO error)    -> WARN, no nudge written (never brick)
#
# Producer contract: this is a SECOND, independent producer of
# .lev/nudges/pending/{timestamp}-{type}.yaml, following the exact schema and
# lifecycle documented at <lev-root>/.lev/nudges/nudge.schema.yaml and
# implemented by Lev's own producer, plugins/system-dashboard/src/nudges.ts
# (writeNudge()). This script does NOT invoke that TS module — no cross-repo
# Node/TS runtime dependency from the CR side — it emits the identical YAML
# shape directly, field-for-field.
#
# Schema-enum honesty: nudge.schema.yaml's `type` enum has no dedicated
# claim-rejection entry (stale_bead, bead_stall, breadth_check,
# blocked_pileup, cdo_reminder, velocity_drop). Per instruction, this script
# reuses the closest existing type rather than inventing one the enum would
# reject:
#   priority 1 (REJECTED)           -> type: blocked_pileup
#   priority 3 (INSUFFICIENT_DEPTH) -> type: cdo_reminder
# See ../LEV_NUDGE_DECLARATION.md for the request to add a dedicated
# `claimgate_reject` (or similar) type to the schema owner's enum.
#
# Constraints honoured:
#   C1 (finitude)         — if pending/ already holds >=20 *.yaml nudges,
#                           WARN and skip the write. Never evicts an
#                           existing nudge to make room.
#   C2 (non-commutation)  — append-only: this script only ever ADDS a new
#                           file. It never reads, edits, or deletes any
#                           other file already in pending/ or archived/.
#   Best-effort           — a missing Lev checkout, a missing pending/ dir,
#                           or a gate tooling error (any exit other than
#                           0/1/3) WARNS to stderr and exits 0. Never bricks
#                           the caller.
#
# Usage: claimgate_to_lev_nudge.sh <receipt.json> [--lev-root <path>]
# Env:   LEV_REPO_ROOT overrides the default Lev checkout (~/GitHub/lev).
set -o pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
repo_root=$(CDPATH= cd -- "$script_dir/../.." && pwd) || exit 2
gate="$script_dir/post_receipt_gate.sh"

receipt=${1-}
if [[ -z "$receipt" ]]; then
  echo "usage: claimgate_to_lev_nudge.sh <receipt.json> [--lev-root <path>]" >&2
  exit 2
fi
shift || true

lev_root="${LEV_REPO_ROOT:-$HOME/GitHub/lev}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lev-root)
      lev_root=${2-}
      shift 2 || { echo "claimgate_to_lev_nudge: --lev-root needs a value" >&2; exit 2; }
      ;;
    *)
      echo "claimgate_to_lev_nudge: unknown arg '$1'" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$receipt" ]]; then
  echo "claimgate_to_lev_nudge: receipt not found: $receipt" >&2
  exit 2
fi
if [[ ! -f "$gate" ]]; then
  echo "claimgate_to_lev_nudge: gate script missing: $gate" >&2
  exit 2
fi

pending_dir="$lev_root/.lev/nudges/pending"
if [[ ! -d "$pending_dir" ]]; then
  echo "claimgate_to_lev_nudge: Lev pending dir absent ($pending_dir) -- warning only, not bricking." >&2
  exit 0
fi

hook_out=$(bash "$gate" "$receipt" 2>&1)
hook_exit=$?

receipt_disp="$receipt"
case "$receipt" in
  "$repo_root"/*) receipt_disp="${receipt#"$repo_root"/}" ;;
esac

case "$hook_exit" in
  0)
    echo "claimgate_to_lev_nudge: post_receipt_gate VERIFIED (exit 0) on $receipt_disp -- no nudge needed." >&2
    exit 0
    ;;
  1)
    type="blocked_pileup"
    priority=1
    message="ClaimGate REJECTED a CR receipt (exit 1, blocking): $receipt_disp -- fix and re-run: node claimgate_plugin/suggest.mjs $receipt_disp"
    ;;
  3)
    type="cdo_reminder"
    priority=3
    message="ClaimGate admitted a CR receipt at tier0, pending deeper audit (exit 3, INSUFFICIENT_DEPTH -- not a rejection): $receipt_disp"
    ;;
  *)
    echo "claimgate_to_lev_nudge: post_receipt_gate tooling/IO error (exit $hook_exit) on $receipt_disp -- warning only, no nudge written." >&2
    exit 0
    ;;
esac

pending_count=$(find "$pending_dir" -maxdepth 1 -name '*.yaml' -type f 2>/dev/null | wc -l | tr -d ' ')
if [[ "$pending_count" -ge 20 ]]; then
  echo "claimgate_to_lev_nudge: pending/ at C1 cap ($pending_count/20) -- skipping write, not evicting any existing nudge." >&2
  exit 0
fi

created=$(python3 -c "
import datetime
n = datetime.datetime.now(datetime.timezone.utc)
print(n.strftime('%Y-%m-%dT%H:%M:%S.') + f'{n.microsecond // 1000:03d}Z')
")
ts=$(printf '%s' "$created" | tr ':.' '--')
filename="${ts}-${type}.yaml"
target="$pending_dir/$filename"

escaped_message=$(printf '%s' "$message" | sed 's/"/\\"/g')

tmp=$(mktemp "${TMPDIR:-/tmp}/claimgate_nudge.XXXXXX")
trap 'rm -f "$tmp"' EXIT
{
  printf 'type: %s\n' "$type"
  printf 'priority: %s\n' "$priority"
  printf 'message: "%s"\n' "$escaped_message"
  printf 'created: "%s"\n' "$created"
  printf 'source: %s\n' "claimgate-post-receipt"
} > "$tmp"

mv "$tmp" "$target"
trap - EXIT
echo "claimgate_to_lev_nudge: wrote nudge -> $target (type=$type priority=$priority, hook_exit=$hook_exit)" >&2
exit 0
