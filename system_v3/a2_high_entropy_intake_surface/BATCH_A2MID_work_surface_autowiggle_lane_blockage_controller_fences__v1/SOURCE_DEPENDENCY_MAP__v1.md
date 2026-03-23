# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_work_surface_autowiggle_lane_blockage_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_work_surface_autowiggle_lane_blockage__v1`

## Parent Artifact Dependencies
- blockage-classification lineage:
  - `CLUSTER_MAP__v1:C1`
  - `CLUSTER_MAP__v1:C2`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T1`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 1`
- raw-extract contradiction lineage:
  - `CLUSTER_MAP__v1:C3`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D5`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 2`
- probe and rescue insufficiency lineage:
  - `CLUSTER_MAP__v1:C1`
  - `CLUSTER_MAP__v1:C3`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`
- fail-closed shell lineage:
  - `CLUSTER_MAP__v1:C4`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 3`
- memo-vs-selector and offload lineage:
  - `CLUSTER_MAP__v1:C5`
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D6`
  - `TENSION_MAP__v1:T8`
  - `TENSION_MAP__v1:T9`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 5`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent already isolates the blockage packet, raw drift, fail-closed shell, and offload workaround tightly enough for a controller-facing reduction
