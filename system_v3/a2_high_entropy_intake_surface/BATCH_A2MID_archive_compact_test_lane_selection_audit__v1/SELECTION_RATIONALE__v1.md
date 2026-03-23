# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_archive_compact_test_lane_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this audit batch exists
- the queued next step targeted `TEST_A1_PACKET_ZIP`
- the live ledger already showed that parent as childed by:
  - `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
- a first correction then pointed at `TEST_REAL_A1_002`
- the live ledger already showed that parent as childed by:
  - `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`
- a second correction then pointed at the state-transition family
- the live ledger already showed those parents as childed by:
  - `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
  - `BATCH_A2MID_archive_chain_b_shell_drift__v1`
  - `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
- a third correction then pointed at the `v2_zipv2` trio through `PACKET_E2E_001`
- the live ledger already showed:
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- the current task is therefore not another packet, `REAL_A1`, resume, state-transition, `PACKET_E2E_001`, or `PACKET_REQ_001` reduction
- it is a compact test-lane selection audit that chooses the real next unresolved family from the live ledger

## Why the earlier compact-test families are no longer the main gap
- the packet microfamily is already childed:
  - `TEST_A1_PACKET_EMPTY`
  - `TEST_A1_PACKET_ZIP`
- the deterministic pair is already childed:
  - `DET_A`
  - `DET_B`
- the `REAL_A1` and resume microfamilies are already childed:
  - `TEST_REAL_A1_001`
  - `TEST_REAL_A1_002`
  - `TEST_RESUME_001`
- the state-transition family is already childed:
  - `TEST_STATE_TRANSITION_CHAIN_A`
  - `TEST_STATE_TRANSITION_CHAIN_B`
  - `TEST_STATE_TRANSITION_MUTATION`
- the `v2_zipv2` packet bootstrap siblings are already childed:
  - `V2_ZIPV2_PACKET_E2E_001`
  - `V2_ZIPV2_PACKET_REQ_001`

## Why the remaining unresolved compact test pool is now only `V2_ZIPV2_REPLAY_001`
- the live ledger no longer leaves any other compact deep-archive test parent unresolved in this local lane
- the only remaining unchilded compact test parent in this slice is:
  - `V2_ZIPV2_REPLAY_001`

## Why `V2_ZIPV2_REPLAY_001` is the strongest next target
- it is still unchilded
- it is now the sole remaining unresolved parent in the compact test lane
- it preserves the strongest remaining contradiction packet in this slice:
  - summary and soak count `3` while events retain only `2`
  - queued third strategy packet is the only trace of step `3`
  - hidden hash bridges across both executed and final layers
  - replay authorship coexisting with real-LLM demand
  - second-step `SCHEMA_FAIL` with partial `S0002` landing
  - packet-facing evidence and kill residue richer than final bookkeeping

## Why no sibling now outranks `REPLAY_001`
- `PACKET_REQ_001` is already reduced as a thinner request-only bootstrap shell
- `PACKET_E2E_001` is already reduced as the cleaner middle/base member of the `v2_zipv2` trio
- no other unresolved sibling remains in this compact test lane slice

## Best next existing intake target
- `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
