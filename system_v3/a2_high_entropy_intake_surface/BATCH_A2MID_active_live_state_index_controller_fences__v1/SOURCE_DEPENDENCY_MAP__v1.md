# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_live_state_index_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_systemv3_active_a2state_live_state_index_packet__v1`

## Parent Artifact Dependencies
- state-store class separation lineage:
  - `CLUSTER_MAP__v1:Cluster A`
  - `CLUSTER_MAP__v1:Cluster B`
  - `CLUSTER_MAP__v1:Cluster C`
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`
- duplicate ingest-index identity lineage:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T1`
- broader `doc_index` classification lineage:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D11`
  - `TENSION_MAP__v1:T2`
  - `TENSION_MAP__v1:T10`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
- doc-card/system-map nonidentity lineage:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D5`
  - `A2_3_DISTILLATES__v1:D6`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `TENSION_MAP__v1:T9`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
- registry-metric noncollapse lineage:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D9`
  - `A2_3_DISTILLATES__v1:D10`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`
- memory-chain semantic-core lineage:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D7`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Comparison Anchors Consulted
- active ingest/promotion boundary comparison:
  - `BATCH_A2MID_active_ingest_promotion_controller_fences__v1`
- archived structural map comparison:
  - `BATCH_A2MID_structural_memory_wayfinding__v1`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the live registries, index surfaces, abstraction overlays, and memory-chain contradictions needed for this bounded reduction
