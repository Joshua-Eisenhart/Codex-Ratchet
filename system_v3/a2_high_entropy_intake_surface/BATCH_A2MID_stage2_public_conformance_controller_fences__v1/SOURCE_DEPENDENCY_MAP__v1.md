# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_stage2_public_conformance_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_systemv3_active_spec_stage2_public_conformance__v1`

## Parent Artifact Dependencies
- delivery and gate-stack lineage:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`
- controller and worker-packet lineage:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D2`
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
- schema and browser-bridge lineage:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`
- conformance drift lineage:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
- public-boundary lineage:
  - `CLUSTER_MAP__v1:Cluster E`
  - `A2_3_DISTILLATES__v1:D5`
  - `TENSION_MAP__v1:T4`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C6`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent already compresses the late spec packet into controller-relevant clusters, distillates, and contradiction signatures
