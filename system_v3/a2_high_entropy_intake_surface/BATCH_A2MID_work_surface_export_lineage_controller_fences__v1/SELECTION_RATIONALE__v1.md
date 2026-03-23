# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_work_surface_export_lineage_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_work_surface_sendpack_to_update_export_lineage__v1` is the next uncovered parent after the active ingest/promotion reduction
- the parent is tightly bounded around one export arc:
  - wrapped Stage-3 sendpack
  - outputs-only return
  - intentionally tiny delta
  - broad update-pack rebound
  - detached checksum sidecars
- it is already contradiction-rich and source-linked, so a second-pass reduction can stay small without rereading raw source families

## Why This Reduction Goal
- bounded goal:
  - isolate only the controller-usable export-lineage rules for:
    - one-file wrapper classification
    - lean return handling
    - small-delta drift-prevention intent
    - broad update-pack rebound as separate class
    - detached checksum-sidecar limits
- excluded for now:
  - later delta/update revision ladders
  - any claim that these exports were applied successfully
  - promotion of any `work/out` packaging into active transport or save law

## Deferred Alternatives
- `BATCH_systemv3_active_a2state_live_state_index_packet__v1`
  - strongest next active sibling once this export-lineage packet is narrowed
- `BATCH_work_surface_delta_update_bootstrap_revision_ladder__v1`
  - strongest direct work-surface follow-on after the first export-lineage batch
- `BATCH_systemv3_active_a1state_brain_and_cartridge_judgment_packet__v1`
  - later active sibling after the remaining `a2_state` live-state/index family is handled
