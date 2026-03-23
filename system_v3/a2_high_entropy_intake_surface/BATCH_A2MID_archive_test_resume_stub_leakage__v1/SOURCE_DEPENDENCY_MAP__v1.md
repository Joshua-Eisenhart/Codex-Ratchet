# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_resume_stub_leakage__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_test_resume_001__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- handoff-floor anchor:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
- adjacent execution anchor:
  - `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`

## Bounded Dependency Reads
- dependency group 1:
  - zero-work external-handoff stub with empty inbox and no lower-loop execution
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
    - `A2_3_DISTILLATES__v1.md:Distillate 1`
    - `CLUSTER_MAP__v1.md:Cluster 1`
    - `TENSION_MAP__v1.md:Tension 5`
- dependency group 2:
  - duplicate save-request emission inside a one-step shell
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary B`
    - `A2_3_DISTILLATES__v1.md:Distillate 2`
    - `CLUSTER_MAP__v1.md:Cluster 2`
    - `TENSION_MAP__v1.md:Tension 1`
- dependency group 3:
  - event-step versus packet-sequence drift without a real second step
  - basis:
    - `A2_3_DISTILLATES__v1.md:Distillate 3`
    - `CLUSTER_MAP__v1.md:Cluster 4`
    - `TENSION_MAP__v1.md:Tension 2`
- dependency group 4:
  - active-runtime absolute path leakage inside archived events
  - basis:
    - `A2_3_DISTILLATES__v1.md:Distillate 4`
    - `CLUSTER_MAP__v1.md:Cluster 3`
    - `TENSION_MAP__v1.md:Tension 3`
- dependency group 5:
  - run-specific outer state hash wrapped around generic sample strategy payload
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
    - `A2_3_DISTILLATES__v1.md:Distillate 5`
    - `CLUSTER_MAP__v1.md:Cluster 5`
    - `TENSION_MAP__v1.md:Tension 4`
    - `TENSION_MAP__v1.md:Tension 6`
- dependency group 6:
  - inert machine state with surviving lexical shell
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 6`

## Non-Dependencies
- no raw archive run reread was needed
- no later state-transition chain batches were reopened
- no active runtime or `a2_state` surfaces were used as authority inputs

