# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- archive floor anchor:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
- sibling execution anchor:
  - `BATCH_A2MID_archive_test_det_a_controller_fences__v1`

## Bounded Dependency Reads
- dependency group 1:
  - archive-only four-lane packet loop retained at minimum scale
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 1`
    - `A2_3_DISTILLATES__v1.md:Distillate 1`
- dependency group 2:
  - summary/soak collapse versus deeper accepted state and inflated event residue
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary B`
    - `CLUSTER_MAP__v1.md:Cluster 2`
    - `TENSION_MAP__v1.md:Tension 1`
    - `TENSION_MAP__v1.md:Tension 2`
- dependency group 3:
  - visible packet lattice versus zeroed sequence ledger
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 3`
    - `A2_3_DISTILLATES__v1.md:Distillate 4`
    - `TENSION_MAP__v1.md:Tension 3`
- dependency group 4:
  - duplicate event inflation at a single step
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 4`
    - `TENSION_MAP__v1.md:Tension 1`
    - `TENSION_MAP__v1.md:Tension 6`
    - `TENSION_MAP__v1.md:Tension 7`
- dependency group 5:
  - same-name strategy packet identity split by location, bytes, and validity
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
    - `A2_3_DISTILLATES__v1.md:Distillate 3`
    - `CLUSTER_MAP__v1.md:Cluster 5`
    - `TENSION_MAP__v1.md:Tension 4`
- dependency group 6:
  - accepted packet spine versus later schema-fail regeneration overlay
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 6`
    - `CLUSTER_MAP__v1.md:Cluster 7`
    - `A2_3_DISTILLATES__v1.md:Distillate 2`
    - `TENSION_MAP__v1.md:Tension 5`
- dependency group 7:
  - final-hash divergence across summary/state, event endpoint, and packet prior-state reference
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 8`
    - `A2_3_DISTILLATES__v1.md:Distillate 5`
    - `TENSION_MAP__v1.md:Tension 6`

## Non-Dependencies
- no raw archive root reread was needed
- no sibling `TEST_REAL_A1_*` or `TEST_RESUME_*` batches were reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs

