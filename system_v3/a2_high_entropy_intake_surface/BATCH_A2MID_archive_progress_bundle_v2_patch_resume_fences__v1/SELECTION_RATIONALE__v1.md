# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_archive_progress_bundle_v2_patch_resume_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this child batch exists
- the v1 progress-bundle child is now complete
- its explicit next target is the v2 sibling revision
- this parent is materially different from v1 because it carries patch-lineage resume semantics and a restored sequence ledger
- the next child therefore has to preserve the v2-specific repair and contradiction packets before moving to the broader bundle sibling

## Why this reduction is bounded this way
- the parent already isolates the least noisy seam:
  - patched continuation export status
  - clean continuation language versus dirty retained state
  - README packet claims versus narrower embedded event proof
  - restored sequence maxima and run-local resume control
  - strong hash and transport residue with missing evidence bodies and omitted control context
  - the handoff to `RUN_FOUNDATION_BATCH_0001_bundle`
- this child therefore preserves patch/resume governance and archive contradiction packets rather than reopening the whole replay family

## Why comparison anchors were chosen
- `BATCH_A2MID_archive_progress_bundle_replay_snapshot_fences__v1`
  - used to preserve the sibling-revision comparison seam and stop v2 from being read as if v1 never existed
- `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1`
  - used to preserve the larger parent-run fence below which both progress bundles sit
- `BATCH_A2MID_archive_migrated_run_root_registry_handoff_fences__v1`
  - used to preserve the broader archive descent chain and keep this patched export below run-root demotion

## Why no raw source reread was needed
- the parent first-pass artifacts already expose:
  - patch README semantics
  - embedded two-step snapshot
  - restored sequence ledger
  - event-ledger undercapture
  - dirty retained state under clean continuation claims
  - missing evidence/context closures
  - the explicit next-step target to the broader bundle sibling
- that is enough to produce a bounded reduction
- exact bundle-sibling detail can stay in the next batch

## Why this is not yet the broader bundle child
- v2 still carries its own reusable contradiction packets:
  - repair language versus partial repair reality
  - clean continuation language versus dirty retained state
  - README packet claims versus event-proof gaps
  - strong hash residue versus missing evidence/context
- preserving those first keeps the next sibling handoff cleaner

## Best next consequence from this child
- the next bounded step can now target:
  - `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_bundle__v1`
- with this child acting as the v2 patch/resume fence below archive demotion, patch-language overread, and evidence-gap overread
