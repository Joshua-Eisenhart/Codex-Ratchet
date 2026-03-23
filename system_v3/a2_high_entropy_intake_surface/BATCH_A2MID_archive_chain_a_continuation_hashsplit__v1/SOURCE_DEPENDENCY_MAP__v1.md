# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_chain_a_continuation_hashsplit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- resume-stub predecessor:
  - `BATCH_A2MID_archive_test_resume_stub_leakage__v1`
- adjacent two-step execution anchor:
  - `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`

## Bounded Dependency Reads
- dependency group 1:
  - two executed transitions with queued third continuation
  - basis:
    - `CLUSTER_MAP__v1.md:Cluster 1`
    - `A2_3_DISTILLATES__v1.md:Distillate 1`
- dependency group 2:
  - replay attribution versus `needs_real_llm true`
  - basis:
    - `A2_3_DISTILLATES__v1.md:Distillate 2`
    - `TENSION_MAP__v1.md` replay-versus-real-LLM demand mismatch from parent summary
- dependency group 3:
  - summary/soak/sequence count three versus only two executed transitions
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md`
    - parent ledger summary
    - `TENSION_MAP__v1.md` first contradiction family
- dependency group 4:
  - final-hash split above last executed event with queued third packet using summary/state final hash as input
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `A2_3_DISTILLATES__v1.md`
    - parent manifest notes
- dependency group 5:
  - second-step schema fail with blank target `NEGATIVE_CLASS`
  - basis:
    - `A2_3_DISTILLATES__v1.md`
    - parent manifest notes
- dependency group 6:
  - second-step `S0002` proposal versus mixed final survivor carryover
  - basis:
    - `A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `A2_3_DISTILLATES__v1.md`
    - parent manifest state and packet summaries
- dependency group 7:
  - exact duplicate ` 3` files and runtime-path leakage as archive residue
  - basis:
    - parent manifest notes
    - `SOURCE_MAP__v1.md`

## Non-Dependencies
- no raw archive run reread was needed
- no `CHAIN_B` parent or later mutation family was reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs

