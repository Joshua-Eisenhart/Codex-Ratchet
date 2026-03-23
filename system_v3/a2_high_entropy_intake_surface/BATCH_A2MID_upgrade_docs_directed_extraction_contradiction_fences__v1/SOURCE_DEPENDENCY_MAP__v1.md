# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_upgrade_docs_directed_extraction_contradiction_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_upgrade_docs_directed_extraction_family_contradiction_reprocess__v1`

## Parent Artifact Dependencies
- directed-extraction pivot lineage:
  - `CLUSTER_MAP__v1:C1`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`
- answer-delta preservation lineage:
  - `CLUSTER_MAP__v1:C8`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
- ZIP transport-core lineage:
  - `CLUSTER_MAP__v1:C2`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T2`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`
- batch-scale, sharding, and phase-signal lineage:
  - `CLUSTER_MAP__v1:C3`
  - `CLUSTER_MAP__v1:C4`
  - `CLUSTER_MAP__v1:C6`
  - `A2_3_DISTILLATES__v1:D5`
  - `A2_3_DISTILLATES__v1:D6`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
- confirmation-semantics contradiction lineage:
  - `CLUSTER_MAP__v1:C5`
  - `CLUSTER_MAP__v1:C7`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent already isolates the six policy seams, answer-version deltas, and ambiguity discipline tightly enough for a controller-facing reduction
