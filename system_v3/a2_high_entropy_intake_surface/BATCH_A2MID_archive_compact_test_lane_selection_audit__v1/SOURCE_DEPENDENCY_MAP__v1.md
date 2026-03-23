# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_archive_compact_test_lane_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batches
- `BATCH_A2MID_archive_signal_lane_closure_audit__v1`
- `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
- `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
- `BATCH_A2MID_archive_test_det_a_controller_fences__v1`
- `BATCH_A2MID_archive_test_det_b_controller_fences__v1`
- `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
- `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`
- `BATCH_A2MID_archive_test_resume_stub_leakage__v1`
- `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
- `BATCH_A2MID_archive_chain_b_shell_drift__v1`
- `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
- `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
- `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- reused parent artifacts:
  - `A2_2_REFINED_CANDIDATES__v1.md`
  - `SELECTION_RATIONALE__v1.md`
  - `MANIFEST.json`

## Parent-batch read
- the signal lane is already direct-child closed and no longer the strongest next move
- the packet microfamily is direct-child closed:
  - `TEST_A1_PACKET_EMPTY`
  - `TEST_A1_PACKET_ZIP`
- the deterministic replay pair is direct-child closed:
  - `DET_A`
  - `DET_B`
- both compact `REAL_A1` parents and the resume stub are already direct-child closed:
  - `TEST_REAL_A1_001`
  - `TEST_REAL_A1_002`
  - `TEST_RESUME_001`
- the state-transition family is already direct-child closed:
  - `TEST_STATE_TRANSITION_CHAIN_A`
  - `TEST_STATE_TRANSITION_CHAIN_B`
  - `TEST_STATE_TRANSITION_MUTATION`
- the `v2_zipv2` packet bootstrap siblings are already direct-child closed:
  - `V2_ZIPV2_PACKET_E2E_001`
  - `V2_ZIPV2_PACKET_REQ_001`

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
- `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
- `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
- `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`

## Candidate dependency map
- `RC1_EARLIER_COMPACT_TEST_FAMILIES_THROUGH_V2_PACKET_REQ_ARE_DIRECT_CHILD_CLOSED`
  - parent dependencies:
    - packet, deterministic, `REAL_A1`, resume, state-transition, and `v2_zipv2` packet-bootstrap child batches listed above
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC2_NEXT_UNRESOLVED_COMPACT_TEST_POOL_NOW_IS_ONLY_V2_ZIPV2_REPLAY_001`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC3_V2_ZIPV2_REPLAY_001_IS_THE_STRONGEST_NEXT_UNRESOLVED_TARGET`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1:TENSION_MAP__v1.md`
    - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
    - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- `RC4_REPLAY_001_NOW_OUTRANKS_PACKET_REQ_AND_PACKET_E2E_ONLY_BECAUSE_THEY_ARE_ALREADY_CHILDED`
  - comparison anchor dependencies:
    - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
    - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
    - `BATCH_INDEX__v1.md`
- `RC5_SOLE_REMAINING_PARENT_STATUS_SHRINKS_ROUTING_AMBIGUITY`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC6_LEDGER_STATE_OVERRIDES_STALE_PACKET_ZIP_REAL_A1_STATE_TRANSITION_AND_PACKET_E2E_QUEUE_TEXT`
  - parent dependencies:
    - `BATCH_A2MID_archive_signal_lane_closure_audit__v1:A2_2_REFINED_CANDIDATES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`

## Quarantine dependency map
- `Q1_DUPLICATE_EARLIER_COMPACT_TEST_REDUCTION`
  - earlier compact-test child batches listed above
- `Q2_TREAT_EARLIER_MICROFAMILY_CLOSURE_AS_TOTAL_DEEP_ARCHIVE_TEST_CLOSURE`
  - `BATCH_INDEX__v1.md`
- `Q3_REOPEN_ALREADY_CHILDED_STATE_TRANSITION_OR_V2_PACKET_BOOTSTRAP_PARENTS`
  - `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
  - `BATCH_A2MID_archive_chain_b_shell_drift__v1`
  - `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- `Q4_TREAT_REPLAY_001_AS_OPTIONAL_WHEN_IT_IS_THE_ONLY_REMAINING_PARENT`
  - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `BATCH_INDEX__v1.md`
- `Q5_TREAT_THIS_ROUTING_AUDIT_AS_ACTIVE_A2_CONTROL_MEMORY`
  - `A2_MID_REFINEMENT_PROCESS__v1.md`
  - `BATCH_INDEX__v1.md`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the needed work here was live-ledger correction and next-family nomination
  - the existing child batches plus the unresolved `REPLAY_001` summaries and tension map were sufficient to determine the next bounded target
