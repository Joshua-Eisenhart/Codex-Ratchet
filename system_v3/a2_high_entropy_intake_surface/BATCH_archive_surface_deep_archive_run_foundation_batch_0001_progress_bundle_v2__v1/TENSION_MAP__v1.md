# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle_v2__v1`
Date: 2026-03-09

## Tension 1: Clean Continuation Claim Versus Dirty Retained State
- source anchors:
  - `README_PATCH_AND_RUN.txt`
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - README and summary preserve a zero-reject/zero-park clean continuation, while state preserves seven parked terms and eleven reject-log entries
- intake handling:
  - keep both as archive truth at different granularities; do not normalize the state into "fully clean"

## Tension 2: README Packet Claim Versus Event-Ledger Coverage
- source anchors:
  - `README_PATCH_AND_RUN.txt`
  - `events.jsonl`
  - `packets/`
- bounded contradiction:
  - README says `000010 + 000011` drove the latest clean continuation, but `events.jsonl` references strategy packets only through `000009` even though `packets/` retains `000010` and `000011`
- intake handling:
  - preserve as an archive packaging gap between operator note, carried packet residue, and embedded event proof

## Tension 3: Strong Hash Integrity Versus Weak Evidence Retention
- source anchors:
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the bundle proves end-state integrity strongly, but repeatedly points at missing runtime `sim/sim_evidence_*` bodies that are not preserved inside the archive object
- intake handling:
  - treat the bundle as reliable state/transport residue with incomplete evidence-body preservation

## Tension 4: Summary Blocker Count Versus State-Level Blocker Encoding
- source anchors:
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - summary reports `unresolved_promotion_blocker_count 7`, but the most explicit blocker-like state residue is a seven-entry `kill_log`; the state surface does not preserve a direct one-field unresolved-blocker mirror
- intake handling:
  - keep the blocker count as summary-level history rather than promoting it to a cleanly grounded state-law field

## Tension 5: Recovered Resume Control Versus Missing Full Run Context
- source anchors:
  - `README_PATCH_AND_RUN.txt`
  - `sequence_state.json`
  - bundle root inventory
- bounded contradiction:
  - v2 explicitly repairs resume behavior around run-local state and sequence maxima, yet the bundle still omits broader run-control surfaces such as `HARDMODE_METRICS.json` and the `sim/` subtree
- intake handling:
  - retain v2 as a partial repair/export artifact, not as a self-sufficient run capsule

