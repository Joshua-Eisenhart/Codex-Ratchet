# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_live_state_index_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_systemv3_active_a2state_live_state_index_packet__v1` is the next uncovered active `a2_state` parent after the export-lineage reduction
- the parent is bounded around the remaining source-like live-state layer:
  - registries and counters
  - ingest indices and classification
  - doc-card/system-map abstractions
  - memory chain and shard continuity
- it is already contradiction-rich and source-linked, so the second pass can stay narrow without rereading raw source families

## Why This Reduction Goal
- bounded goal:
  - isolate only the controller-usable rules for:
    - separate active state-store classes
    - duplicate-index equivalence without artifact collapse
    - broader `doc_index` classification scope
    - doc-card/system-map overlay nonidentity
    - noncollapse of registry counts into one metric
    - memory-chain semantic signal versus autosave churn
- excluded for now:
  - direct mutation of any active `a2_state` file
  - general `a1_state` judgment work
  - cross-family arithmetic unification across campaign, constraint, rosetta, and autosave surfaces

## Deferred Alternatives
- `BATCH_systemv3_active_a1state_brain_and_cartridge_judgment_packet__v1`
  - strongest next active sibling once the source-like `a2_state` sweep is narrowed
- `BATCH_work_surface_delta_update_bootstrap_revision_ladder__v1`
  - strongest direct work-surface follow-on if the queue returns to export revision archaeology
- `BATCH_systemv3_active_a1state_entropy_control_pack_family__v1`
  - later active sibling after the first `a1_state` judgment packet
