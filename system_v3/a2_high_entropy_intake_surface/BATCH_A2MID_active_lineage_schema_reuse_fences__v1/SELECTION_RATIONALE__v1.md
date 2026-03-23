# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_lineage_schema_reuse_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_systemv3_active_lineage_integrity_audit__v1` is the strongest verification-side packet in the active-system chain after the semantic reductions are already complete
- the parent is bounded in the right way for one A2-mid pass:
  - it verifies the active packet chain without reopening raw source families
  - it preserves structural completeness and reduction layering
  - it keeps manifest-schema heterogeneity explicit rather than normalizing it away
  - it restates safe reuse limits for the operator-facing layers

## Why This Reduction Goal
- bounded goal:
  - isolate the highest-value verification-side fences for:
    - active-chain completeness
    - clear but heterogeneous lineage encoding
    - stable contradiction-corridor continuity
    - tiered reuse and reopen-parent discipline
    - the rule that audit-side packets verify but do not replace authority
- excluded for now:
  - manifest-bridge normalization
  - reader-contract formalization
  - validator fixtures
  - any raw source-family reread, runtime work, or control-surface mutation

## Deferred Alternatives
- `BATCH_systemv3_active_manifest_lineage_bridge__v1`
  - strongest next bridge packet once the audit-side fences are preserved
- `BATCH_systemv3_active_manifest_reader_contract__v1`
  - strongest later reader-contract packet after the bridge layer
- `BATCH_systemv3_active_manifest_validator_fixture_matrix__v1`
  - strongest later fixture packet once bridge and reader-contract layers are narrowed
