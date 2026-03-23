# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_archive_signal_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batches
- `BATCH_A2MID_archive_signal_0002_failclosed_promotion_hashdrift_fences__v1`
- `BATCH_A2MID_archive_signal_0003_negative_residue_hashdrift_fences__v1`
- `BATCH_A2MID_archive_signal_0004_summary_replay_audit_fences__v1`
- `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
- `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`
- reused parent artifacts:
  - `A2_2_REFINED_CANDIDATES__v1.md`
  - `SELECTION_RATIONALE__v1.md`
  - `CONTRADICTION_PRESERVATION__v1.md`
  - `DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
  - `MANIFEST.json`

## Parent-batch read
- the deep-archive `RUN_SIGNAL` lane is direct-child closed across raw `0002` through raw `0005`
- the `0005_bundle` sibling also has a direct child and closes the bundle-side controller seam
- no stronger default signal-family re-entry target remains after those five children

## Control-surface dependencies read but not mutated
- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
- `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_MID_REFINEMENT_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`

## Comparison anchors
- `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
- `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
- `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1`
- `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
- `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
- `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
- `BATCH_archive_surface_deep_archive_test_resume_001__v1`
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
- `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`

## Candidate dependency map
- `RC1_RUN_SIGNAL_LANE_0002_TO_0005_PLUS_BUNDLE_IS_DIRECT_CHILD_CLOSED`
  - parent dependencies:
    - `BATCH_A2MID_archive_signal_0002_failclosed_promotion_hashdrift_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
    - `BATCH_A2MID_archive_signal_0003_negative_residue_hashdrift_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
    - `BATCH_A2MID_archive_signal_0004_summary_replay_audit_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
    - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
    - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC2_SIGNAL_REENTRY_IS_NO_LONGER_THE_STRONGEST_DEEP_ARCHIVE_GAP`
  - parent dependencies:
    - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
    - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC3_NEXT_UNRESOLVED_POOL_NOW_SITS_IN_COMPACT_TEST_FAMILIES`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_real_a1_001__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_real_a1_002__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_resume_001__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC4_TEST_A1_PACKET_ZIP_IS_THE_STRONGEST_NEXT_UNRESOLVED_TARGET`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1:TENSION_MAP__v1.md`
    - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
- `RC5_PACKET_ZIP_OUTRANKS_REAL_A1_002_AND_BROADER_STATE_TRANSITION_REENTRY`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_real_a1_002__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
- `RC6_LEDGER_STATE_OVERRIDES_STALE_FOLDER_ORDER_OR_NEXT_NUMBER_MOMENTUM`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`

## Quarantine dependency map
- `Q1_REOPEN_SIGNAL_0002_TO_0005_BY_DEFAULT`
  - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
  - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
- `Q2_TREAT_RAW_0005_OR_0005_BUNDLE_AS_GLOBAL_DEEP_ARCHIVE_CLOSURE`
  - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
  - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
- `Q3_PICK_NEXT_TARGET_BY_LEXICAL_OR_NUMERIC_MOMENTUM`
  - `BATCH_INDEX__v1.md`
- `Q4_TREAT_PACKET_EMPTY_CHILD_AS_IF_IT_ALREADY_CLOSED_PACKET_ZIP`
  - `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
  - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
- `Q5_TREAT_THIS_ROUTING_AUDIT_AS_ACTIVE_A2_CONTROL_MEMORY`
  - `A2_MID_REFINEMENT_PROCESS__v1.md`
  - `BATCH_INDEX__v1.md`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the needed work here was lane-state audit and next-family nomination, not raw-source recovery
  - the live ledger, the completed signal children, and the unresolved test-family summaries were sufficient to determine the next bounded target
