# ClaimGate to Lev nudge declaration

This is a declaration for the Lev dev. It documents a new producer of
`.lev/nudges/pending/` entries. It does not admit or wire anything on the
Lev side.

## What this is

`claimgate_plugin/hooks/claimgate_to_lev_nudge.sh` is a second, independent
producer of Lev's orchestrator-to-orchestrator nudge surface
(`.lev/nudges/nudge.schema.yaml`, currently written only by
`plugins/system-dashboard/src/nudges.ts`). It gives ClaimGate a Lev-native
enforcement leg alongside the existing CR git leg
(`claimgate_plugin/hooks/pre_commit_gate_receipts.sh`): when a CR ratchet
receipt is rejected or under-audited, a nudge lands in Lev's own signal
surface, independent of whether the receipt is ever committed to CR's git.

Usage:

```
claimgate_to_lev_nudge.sh <receipt.json> [--lev-root <path>]
```

Default `--lev-root` is `~/GitHub/lev` (override with `LEV_REPO_ROOT`).

## Exit-code to priority map

`claimgate_to_lev_nudge.sh` runs `post_receipt_gate.sh <receipt.json>` and
maps its exit code:

| post_receipt_gate.sh exit | Meaning | Nudge |
|---|---|---|
| 0 | VERIFIED | none written |
| 1 | REJECTED | priority 1 (urgent, blocking) |
| 3 | INSUFFICIENT_DEPTH (admitted, not a rejection) | priority 3 (informational) |
| other | tooling/IO error | none written, warns to stderr |

## Producer interface used

The script writes the YAML shape directly (matching
`nudges.ts` `writeNudge()` field for field) rather than invoking that TS
module. This avoids a cross-repo Node/TS runtime dependency from the CR
side. Filename convention matches exactly:
`{created, ':' and '.' replaced by '-'}-{type}.yaml`.

Fields written: `type`, `priority`, `message`, `created`, `source`. `source`
is set to `claimgate-post-receipt` so a future consumer can tell this nudge
apart from the dashboard's own. `context` is omitted — none of the schema's
documented `context` properties (`bead_ids`, `stall_ticks`,
`velocity_current`, and so on) fit a ClaimGate verdict, so the receipt path
and fix command are carried in `message` instead, to stay strictly inside
the documented schema shape.

Constraints honoured:

- C1 (finitude) — if `pending/` already holds 20 or more `*.yaml` files, the
  script warns and skips the write. It never evicts an existing nudge to
  make room (Lev's own writer does evict the oldest at capacity; this
  producer does not reimplement that, to stay strictly append-only).
- C2 (non-commutation) — append-only. The script only ever adds a new file.
  It never reads, edits, or deletes any other file in `pending/` or
  `archived/`.
- Best-effort — a missing Lev checkout, a missing `pending/` directory, or
  a gate tooling error all warn and exit 0. The script never bricks its
  caller.

## Request: a dedicated nudge type

`nudge.schema.yaml`'s `type` enum has six values (`stale_bead`,
`bead_stall`, `breadth_check`, `blocked_pileup`, `cdo_reminder`,
`velocity_drop`), none of which name a claim verdict. Per the build
instruction, this producer reuses the closest existing type rather than
inventing one the enum would reject:

- priority 1 (REJECTED) borrows `blocked_pileup` — closest existing
  semantics to "a claim is blocked from admission".
- priority 3 (INSUFFICIENT_DEPTH) borrows `cdo_reminder` — closest existing
  semantics to "needs attention, not urgent".

Neither is a real fit. The request: add a dedicated type, for example
`claimgate_reject`, to the schema's enum, so a future consumer can
distinguish a ClaimGate verdict from a bead-tracking nudge without parsing
`message` text. This file does not edit `nudge.schema.yaml` — that edit is
the Lev dev's to make.

## Honest finding: no consumer exists yet

Before building this, the round-trip's consume side was checked
independently (grep across `~/GitHub/lev` and the CR-facing
`~/lev-main/.worktrees/current-main-20260715` checkout, a read of
`.lev/hooks/heartbeat.flow.yaml` and `heartbeat.sh`, a read of
`plugins/system-dashboard/src/render/*`, and `lev events tail` before and
after a live test write). The result: nothing in Lev today reads
`.lev/nudges/pending/`. The only code anywhere in the repo that ever lists
that directory is `writeNudge()`'s own internal dedupe/eviction check
(`plugins/system-dashboard/src/nudges.ts` and its duplicate,
`tick-original.mjs`) — a write-path check, not a consumer. `heartbeat.sh`
does not reference nudges at all; it only runs the pulse scan/refresh. The
dashboard's render layer does not display pending nudges. No `lev events
tail` entry appears for a nudge file write — `writeNudge()` uses plain
`fs.writeFileSync`, not the event bus.

This means the round trip this build was asked to demonstrate has two
legs: ClaimGate write (done, verified live) and Lev consume (not
buildable from the CR side — there is nothing on the Lev side to
demonstrate against). The write leg was verified live 2026-07-22 against
the real `~/GitHub/lev` checkout: a nudge from the known-rejecting fixture
`claimgate_plugin/fixtures/hook_inflated_receipt.json` landed in
`.lev/nudges/pending/`, was confirmed schema-valid and byte-identical to
the other four pre-existing nudges' shape, then was acknowledged and moved
to `.lev/nudges/archived/` per the documented lifecycle as cleanup (left in
place, named
`2026-07-22T09-34-49-690Z-blocked_pileup.yaml`,
`acknowledged_by: claimgate-nudge-roundtrip-demo-cleanup` — safe to delete
if unwanted).

Request: wire something — `heartbeat.flow.yaml`, a stop-hook, or the
dashboard render — to read `.lev/nudges/pending/` and act on priority-1
entries, so the write leg this producer now supplies actually closes the
loop. Until then, a ClaimGate rejection is visible in Lev's filesystem but
invisible to any running Lev process.
