# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_control_spine_controller_boundaries__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_systemv3_active_root_spec_control_spine__v1`

## Parent Artifact Dependencies
- repo-shape and mutation gate lineage:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C6`
- owner-model and mutation-geometry lineage:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_3_DISTILLATES__v1:D4`
- helper-surface quarantine lineage:
  - `CLUSTER_MAP__v1:Cluster C`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`
- active-A2 boundary lineage:
  - `A2_3_DISTILLATES__v1:D6`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
- transport split lineage:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`
- unresolved but preserved quarantine lineage:
  - `TENSION_MAP__v1:T1`
  - `TENSION_MAP__v1:T3`
  - `A2_3_DISTILLATES__v1:D9`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent already isolates the low-entropy control-spine clusters, reusable distillates, and contradiction signatures needed for this bounded controller-facing reduction
