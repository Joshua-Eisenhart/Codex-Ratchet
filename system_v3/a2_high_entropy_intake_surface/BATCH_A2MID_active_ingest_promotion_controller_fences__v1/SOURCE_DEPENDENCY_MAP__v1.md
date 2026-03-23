# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_ingest_promotion_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_systemv3_active_a2state_ingest_validation_promotion_packet__v1`

## Parent Artifact Dependencies
- heterogeneous ingest lineage:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T1`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`
- fail-closed rosetta lineage:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D5`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
- lane triage and family-promotion boundary lineage:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D6`
  - `A2_3_DISTILLATES__v1:D7`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T6`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
- excluded-evidence promotion-audit lineage:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D11`
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C7`
- mixed-pass and debt nonclosure lineage:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D9`
  - `TENSION_MAP__v1:T8`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`
- full-surface classification cross-check lineage:
  - `CLUSTER_MAP__v1:Cluster E`
  - `A2_3_DISTILLATES__v1:D10`
  - `TENSION_MAP__v1:T9`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Comparison Anchors Consulted
- active A2 controller-boundary comparison:
  - `BATCH_A2MID_active_a2state_controller_admission_fences__v1`
- active control-spine comparison:
  - `BATCH_A2MID_active_control_spine_controller_boundaries__v1`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the ingest packet family, promotion contracts/audits, and mixed audit claims needed for this bounded reduction
