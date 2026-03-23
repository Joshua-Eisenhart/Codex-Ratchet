# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_work_surface_export_lineage_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_work_surface_sendpack_to_update_export_lineage__v1`

## Parent Artifact Dependencies
- wrapped sendset lineage:
  - `CLUSTER_MAP__v1:C1`
  - `A2_3_DISTILLATES__v1:D1`
  - `TENSION_MAP__v1:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 1`
- lean return lineage:
  - `CLUSTER_MAP__v1:C2`
  - `A2_3_DISTILLATES__v1:D2`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 2`
- minimal delta lineage:
  - `CLUSTER_MAP__v1:C3`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T3`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 3`
- broad update-pack rebound lineage:
  - `CLUSTER_MAP__v1:C4`
  - `A2_3_DISTILLATES__v1:REBLOAT_AFTER_MINIMAL_DELTA`
  - `A2_3_DISTILLATES__v1:OVERLAY_BOUNDARY_BLUR`
  - `TENSION_MAP__v1:T2`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 4`
- detached checksum-sidecar lineage:
  - `CLUSTER_MAP__v1:C5`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate 5`

## Comparison Anchors Consulted
- upstream sendpack comparison:
  - `BATCH_A2MID_work_surface_stage3_sendpack_controller_fences__v1`
- archived export-pack packaging comparison:
  - `BATCH_A2MID_export_pack_restart_bundle__v1`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the wrapped export arc, checksum conventions, and scope-oscillation contradictions needed for this bounded reduction
