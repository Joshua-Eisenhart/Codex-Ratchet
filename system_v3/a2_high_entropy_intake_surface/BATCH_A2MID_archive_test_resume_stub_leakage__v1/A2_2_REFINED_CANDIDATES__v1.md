# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_resume_stub_leakage__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_RESUME_001_IS_A_ZERO_WORK_EXTERNAL_HANDOFF_STUB`
- candidate read:
  - controller reads should preserve `TEST_RESUME_001` as a zero-work external-handoff stub:
    - stop reason `A1_NEEDS_EXTERNAL_STRATEGY`
    - empty `a1_inbox/`
    - no accepted, parked, rejected, sim, survivor, or ledger state
  rather than as a lower-loop execution run
- why candidate:
  - this is the parent's clearest boundary-role rule
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
  - `A2_3_DISTILLATES__v1.md:Distillate 1`
  - `CLUSTER_MAP__v1.md:Cluster 1`
  - `TENSION_MAP__v1.md:Tension 5`

## Candidate RC2: `DUPLICATE_SAVE_REQUEST_EMISSION_SURVIVES_INSIDE_A_ONE_STEP_SHELL`
- candidate read:
  - controller reads should preserve that summary reports one step while the archive retains:
    - two `a1_strategy_request_emitted` rows
    - two outbound `A0_TO_A1_SAVE_ZIP` packets
  and both event rows still remain at `step 1`
- why candidate:
  - this is the parent's strongest request-duplication contradiction
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary B`
  - `A2_3_DISTILLATES__v1.md:Distillate 2`
  - `CLUSTER_MAP__v1.md:Cluster 2`
  - `TENSION_MAP__v1.md:Tension 1`

## Candidate RC3: `PACKET_SEQUENCE_CAN_ADVANCE_WITHOUT_REAL_STEP_PROGRESSION`
- candidate read:
  - controller reads should preserve that the second outbound save packet changes only the header sequence from `1` to `2`, while both save summaries still report `step 1` and the run does not acquire a real second step
- why candidate:
  - this is the parent's cleanest event-step versus packet-sequence seam
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md:Distillate 3`
  - `CLUSTER_MAP__v1.md:Cluster 4`
  - `TENSION_MAP__v1.md:Tension 2`

## Candidate RC4: `ARCHIVED_EVENTS_CAN_LEAK_ACTIVE_RUNTIME_PATHS`
- candidate read:
  - controller reads should preserve the event ledger's `system_v3/runtime/...` packet paths as historical provenance leakage, not rewrite them into archive-local paths and not treat them as live runtime authority
- why candidate:
  - this is the parent's strongest archive-versus-live-path seam
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md:Distillate 4`
  - `CLUSTER_MAP__v1.md:Cluster 3`
  - `TENSION_MAP__v1.md:Tension 3`

## Candidate RC5: `REAL_OUTER_STATE_HASH_CAN_WRAP_A_GENERIC_SAMPLE_SAVE_PAYLOAD`
- candidate read:
  - controller reads should preserve that the outer run and save summary bind to the real hash `de0e5fe9...`, while the embedded save payload remains generic:
    - `STRAT_SAMPLE_0001`
    - placeholder digest fields
    - all-zero inner input state hash
  so the packet is a sample resume scaffold, not earned strategy output
- why candidate:
  - this is the parent's strongest payload-layer mismatch
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
  - `A2_3_DISTILLATES__v1.md:Distillate 5`
  - `CLUSTER_MAP__v1.md:Cluster 5`
  - `TENSION_MAP__v1.md:Tension 4`
  - `TENSION_MAP__v1.md:Tension 6`

## Candidate RC6: `OPERATIONAL_COLLAPSE_DOES_NOT_ERASE_THE_LEXICAL_SHELL`
- candidate read:
  - controller reads should preserve that the machine state is operationally empty while lexical and formula shell surfaces still remain populated:
    - `derived_only_terms`
    - `formula_glyph_requirements`
    - `l0_lexeme_set`
- why candidate:
  - this is the parent's cleanest shell-versus-operation split
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 6`

## Quarantined Q1: `A1_SOURCE_PACKET_AS_PROOF_THAT_AN_INBOUND_STRATEGY_RETURNED`
- quarantine read:
  - do not treat summary field `a1_source packet` as proof that an inbound A1 packet returned or was retained locally
- why quarantined:
  - the parent explicitly preserves an empty inbox and only outbound save zips
- parent dependencies:
  - `TENSION_MAP__v1.md:Tension 5`
  - `CLUSTER_MAP__v1.md:Cluster 1`

## Quarantined Q2: `SEQUENCE_2_SAVE_PACKET_AS_PROOF_OF_A_REAL_SECOND_STEP`
- quarantine read:
  - do not let the second save packet or its header sequence `2` retell the run as a real second completed step
- why quarantined:
  - the parent explicitly preserves both event rows and both save summaries at `step 1`
- parent dependencies:
  - `TENSION_MAP__v1.md:Tension 1`
  - `TENSION_MAP__v1.md:Tension 2`
  - `CLUSTER_MAP__v1.md:Cluster 2`
  - `CLUSTER_MAP__v1.md:Cluster 4`

## Quarantined Q3: `SAMPLE_SAVE_PAYLOAD_AS_EARNED_OR_TRUSTED_RUNTIME_PROVENANCE`
- quarantine read:
  - do not promote the embedded sample strategy, placeholder hashes, or zero inner input state hash into earned strategy output or trusted provenance
- why quarantined:
  - the parent explicitly preserves the payload as generic scaffold wrapped in run-specific outer metadata
- parent dependencies:
  - `TENSION_MAP__v1.md:Tension 4`
  - `TENSION_MAP__v1.md:Tension 6`
  - `CLUSTER_MAP__v1.md:Cluster 5`

