# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_refinedfuel_thread_s_full_save_family__v1`
Extraction mode: `SAVE_KIT_PASS`

## T1) Replay-complete Thread-S framing vs current save-boundary doctrine
- source markers:
  - source 1: `6-16`
  - source 8: `1-5`
- comparison markers:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md:126-138`
- tension:
  - the readme says this bundle contains everything Thread S needs to archive/replay the current Thread B state
  - active A2 state now says save ZIPs are informational only and lower-loop mutation remains governed by stricter transport surfaces
- preserved read:
  - keep the kit as artifact-continuity lineage, not as present transport authority

## T2) File-integrity hashing vs empty ruleset / megaboot hash posture
- source markers:
  - source 4: `1-7`
  - source 3: `5-13`
- tension:
  - the family carries a complete per-file `SHA256SUMS` surface
  - the policy state simultaneously records:
    - `ACTIVE_RULESET_SHA256_EMPTY TRUE`
    - `ACTIVE_MEGABOOT_SHA256_EMPTY TRUE`
    - header-required flags as `FALSE`
- preserved read:
  - preserve the kit as hash-aware packaging, but not as a fully locked authority chain

## T3) Snapshot portability vs newer structured run-surface layout
- source markers:
  - source 8: `1-5`
  - source 8: `2156-2160`
- comparison markers:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md:56-85`
- tension:
  - the family is designed as a portable replay pack centered on one snapshot plus sidecars
  - the newer run contract splits persistent state across:
    - `snapshots/`
    - `sim/`
    - `tapes/`
    - `logs/`
    - lean `state.json` surfaces
- preserved read:
  - keep the family as an older compact packaging strategy, not as the current filesystem contract

## T4) One canonical snapshot container vs intentional sidecar duplication
- source markers:
  - source 1: `9-16`
  - source 7: `1-60`
  - source 8: `1-30`
- tension:
  - the readme calls `THREAD_S_SAVE_SNAPSHOT_v2.txt` the canonical snapshot container
  - the family also ships separate ledger-body and term dumps that partially restate the same state at higher detail
- preserved read:
  - treat the sidecars as deliberate inspection aids, not as accidental duplication or batch noise

## T5) Massive operational term menu vs explicit noncanonical term status
- source markers:
  - source 5: `13-21`
  - source 6: `7-15`
  - source 6: `202-270`
  - source 1: `18-20`
- tension:
  - the save indexes `264` active term defs and the dump enumerates a very broad `auto_*` operational vocabulary
  - the readme explicitly says the registry is `TERM_PERMITTED` only and excludes `LABEL_PERMITTED` / `CANONICAL_ALLOWED`
- preserved read:
  - preserve the menu as archived registry evidence, not as active semantic admission

## T6) Clean checkpoint posture vs the appearance of total replay completeness
- source markers:
  - source 1: `18-20`
  - source 5: `279-282`
  - source 7: `1877-1880`
  - source 8: `1877-1878`
  - source 8: `2151-2158`
- tension:
  - the family presents itself as a replay-complete save kit
  - the actual state it captures is a particularly quiet checkpoint:
    - empty park set
    - empty evidence pending
    - `STATE_CHANGE: NONE`
    - unchanged-ledger streak `0`
- preserved read:
  - read this as a zero-pending checkpoint snapshot, not as a general proof that all replay states look this clean

## T7) Archived Thread-S transport semantics vs current ordered ZIP/tape consolidation
- source markers:
  - source 1: `6-16`
  - source 8: `2156-2160`
- comparison markers:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md:130-157`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md:5-14`
- tension:
  - the kit assumes a direct Thread-S-side archive/replay handoff model
  - the current active architecture describes ordered ZIP-mediated lanes with explicit consolidation, `EXPORT_BLOCK`, `SIM_EVIDENCE`, and run-surface partitioning
- preserved read:
  - preserve the historical externalization pattern without letting the older Thread-S handoff semantics override current transport law
