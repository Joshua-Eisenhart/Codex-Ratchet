# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_archive_progress_bundle_replay_snapshot_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this child batch exists
- the parent run child is now complete
- its explicit next derived surface is the first progress bundle
- this parent is structurally different enough from the full run that it should not remain only a first-pass archive map
- the next child therefore has to preserve the replay/export-specific contradictions before moving to the v2 sibling

## Why this reduction is bounded this way
- the parent already isolates the cleanest seam:
  - replay/export-kit status
  - cumulative README replay narrative
  - narrow embedded one-step snapshot
  - duplicated carried strategy lanes
  - selective event trace
  - retained failure residue below zeroed top lines
  - missing sim evidence bodies
- this child therefore preserves replay/export governance and compression contradictions rather than reflattening the whole bundle

## Why comparison anchors were chosen
- `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1`
  - used to preserve the full parent-run fence below which this replay export sits
- `BATCH_A2MID_archive_migrated_run_root_registry_handoff_fences__v1`
  - used to preserve the larger archive descent chain and keep this child below run-root demotion
- `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle_v2__v1`
  - used to keep the next-step handoff aimed at the patched continuation sibling instead of at an ad hoc later target

## Why no raw source reread was needed
- the parent first-pass artifacts already expose:
  - bundle triad structure
  - README replay semantics
  - embedded snapshot counts
  - short event ledger references
  - packet and consumed-strategy duplication
  - omission of heavier control surfaces and sim evidence
  - the explicit next-step target to `v2`
- that is enough to produce a bounded reduction
- exact sibling-comparison detail can stay in the next batch

## Why this is not yet the v2 sibling child
- the first progress bundle still carries its own reusable contradiction packets:
  - cumulative replay narrative versus one-step snapshot
  - replay material broader than replay history
  - failure residue below zeroed top lines
  - retained trace references above missing evidence bodies
- preserving those first makes the v1-to-v2 comparison cleaner

## Best next consequence from this child
- the next bounded step can now target:
  - `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle_v2__v1`
- with this child acting as the v1 replay/export fence below archive demotion, snapshot compression, and evidence-gap overread
