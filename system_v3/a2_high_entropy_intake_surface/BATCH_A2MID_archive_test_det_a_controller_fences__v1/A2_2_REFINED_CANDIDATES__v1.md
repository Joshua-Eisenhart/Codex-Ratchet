# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_det_a_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_DET_A_PRESERVES_A_REAL_TWO_STEP_EXECUTION_SPINE_WITH_A_QUEUED_THIRD_CONTINUATION`
- candidate read:
  - controller reads should preserve that `TEST_DET_A` has two executed packet cycles while the third step survives only as a queued A1 continuation packet
- why candidate:
  - this is the parent's strongest executed-versus-queued boundary
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:2`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC2: `SUMMARY_STATE_FINAL_HASH_OUTRANKS_THE_LAST_EXECUTED_EVENT_ENDPOINT_WITHOUT_ERASING_IT`
- candidate read:
  - controller reads should preserve the summary/state sidecar as the stronger final snapshot, while keeping the last executed event endpoint visibly distinct and earlier
- why candidate:
  - this is the parent's clearest closure-layer authority fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Candidate RC3: `REPLAY_AUTHORED_A1_LINEAGE_SURVIVES_ONLY_IN_TRANSPORT_NOT_IN_INBOX`
- candidate read:
  - controller reads should preserve replay-authored A1 lineage as transport-only residue because the inbox is empty and all A1 strategy history survives only in `zip_packets/`
- why candidate:
  - this is the parent's cleanest lineage-channel boundary
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:4`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC4: `ZERO_PACKET_PARKS_DO_NOT_ELIMINATE_PARKED_PROMOTION_DEBT`
- candidate read:
  - controller reads should preserve that clean packet transport does not resolve semantic promotion debt because state still keeps three `PARKED` sim promotion states and three unresolved blockers
- why candidate:
  - this is the parent's strongest anti-clean-counter overread
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:5`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC5: `OPERATOR_EXHAUSTION_AND_SCHEMA_FAIL_FORM_A_FAIL_CLOSED_STOP_BOUNDARY_DESPITE_A_PRESERVED_NEXT_STEP_PACKET`
- candidate read:
  - controller reads should preserve `A2_OPERATOR_SET_EXHAUSTED` plus `SCHEMA_FAIL` as a fail-closed stop boundary, while also preserving the queued third strategy packet as a visible but unexecuted next-step proposal
- why candidate:
  - this is the parent's narrowest controller fence for bounded exhaustion without silent truncation
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:6`
  - `MANIFEST.json`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q1: `THREE_COMPLETED_STEPS_AS_PROOF_THAT_STEP_THREE_WAS_EXECUTED`
- quarantine read:
  - do not flatten the third step into executed history when the event ledger and canonical ledger preserve only two executed steps
- why quarantined:
  - the parent preserves the third step as queued continuation state, not executed transport
- parent dependencies:
  - `TENSION_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Quarantined Q2: `EMPTY_INBOX_AS_PROOF_THAT_NO_A1_LINEAGE_SURVIVED`
- quarantine read:
  - do not infer absence of A1 lineage from the empty inbox when the strategy lineage survives under `zip_packets/`
- why quarantined:
  - the parent explicitly preserves replay-authored transport-only lineage
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:4`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q3: `ZERO_PACKET_PARKS_AS_PROOF_OF_SEMANTIC_CLOSURE`
- quarantine read:
  - do not treat zero parked packets as proof that promotion truth has closed
- why quarantined:
  - state still preserves parked promotion outcomes and unresolved blockers
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:5`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q4: `QUEUED_THIRD_STRATEGY_PACKET_AS_PERMISSION_TO_RETELL_THIS_RUN_AS_A_THREE_STEP_SUCCESS`
- quarantine read:
  - do not let the preserved next-step packet convert a fail-closed operator-exhaustion stop into a completed three-step success story
- why quarantined:
  - the parent keeps the stop boundary and the queued continuation together as a bounded contradiction pair
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:6`
