# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_ingest_promotion_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_systemv3_active_a2state_ingest_validation_promotion_packet__v1` is the first uncovered active `a2_state` parent after the already-reduced Stage-3 sendpack batch
- the parent is tightly bounded around one active control topic:
  - how extracted returns are retained
  - how fail-closed rosetta behavior is preserved
  - how runnable lanes and promotion claims are bounded
  - how repo-wide PASS claims coexist with unresolved debt
- it is already contradiction-rich and source-linked, so a second-pass reduction can stay narrow without rereading raw source families

## Why This Reduction Goal
- bounded goal:
  - isolate only the controller-usable rules for:
    - heterogeneous ingest retention
    - fail-closed absence preservation
    - runnable-vs-proposal-vs-edge lane triage
    - source-bound reading of promotion audits on excluded evidence
    - PASS-vs-debt nonclosure handling
    - full-surface audit as cross-check rather than superseding authority
- excluded for now:
  - direct mutation of active A2/A1 stores
  - reread of excluded `runs/` or `run_anchor_surface/` evidence
  - the next live-state/index/doc-card packet family

## Deferred Alternatives
- `BATCH_systemv3_active_a2state_live_state_index_packet__v1`
  - strongest next `a2_state` sibling once this ingest/promotion packet is narrowed
- `BATCH_work_surface_sendpack_to_update_export_lineage__v1`
  - strongest work-surface transport follow-on after the upstream sendpack packet
- `BATCH_systemv3_active_a1state_brain_and_cartridge_judgment_packet__v1`
  - best next active sibling after the remaining `a2_state` live-state/index family is handled
