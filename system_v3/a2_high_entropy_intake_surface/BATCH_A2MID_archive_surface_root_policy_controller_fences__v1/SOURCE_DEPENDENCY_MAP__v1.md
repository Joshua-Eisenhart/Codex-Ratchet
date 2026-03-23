# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_surface_root_policy_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_root_policy_lineage__v1`

## Parent Artifact Dependencies
- archive-only boundary lineage:
  - `CLUSTER_MAP__v1:Cluster 1`
  - `A2_3_DISTILLATES__v1:D1`
  - `TENSION_MAP__v1:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`
- demotion and residue-thinning lineage:
  - `CLUSTER_MAP__v1:Cluster 2`
  - `A2_3_DISTILLATES__v1:D5`
  - `TENSION_MAP__v1:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`
- generated mirror nonauthority lineage:
  - `CLUSTER_MAP__v1:Cluster 3`
  - `A2_3_DISTILLATES__v1:D3`
  - `A2_3_DISTILLATES__v1:D4`
  - `TENSION_MAP__v1:T1`
  - `TENSION_MAP__v1:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`
- tier-specific archive routing lineage:
  - `CLUSTER_MAP__v1:Cluster 5`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_3_DISTILLATES__v1:D7`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T6`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C4`
- historical maturity snapshot lineage:
  - `CLUSTER_MAP__v1:Cluster 4`
  - `A2_3_DISTILLATES__v1:D6`
  - `TENSION_MAP__v1:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Raw Source Reread Status
- raw source reread needed: `false`
- reason:
  - the parent already isolates the archive-root boundary, demotion, mirror, topology, and historical-maturity packet tightly enough for a controller-facing reduction
