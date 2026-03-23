# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_det_b_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_DET_B_PRESERVES_A_REAL_TWO_STEP_EXECUTION_SPINE_WITH_A_QUEUED_THIRD_CONTINUATION`
- candidate read:
  - controller reads should preserve that `TEST_DET_B` has two executed packet cycles while the third step survives only as a queued A1 continuation packet
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
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Candidate RC3: `REPLAY_STRATEGY_LINEAGE_LIVES_IN_ZIP_PACKETS_AND_A1_STRATEGIES_2_IS_ONLY_PACKAGING_RESIDUE`
- candidate read:
  - controller reads should preserve that replay-authored A1 lineage survives only in `zip_packets/`, while the empty root-level `a1_strategies 2/` directory remains packaging noise rather than a second strategy surface
- why candidate:
  - this is the parent's cleanest lineage-versus-packaging fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:7`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC4: `THE_PRESERVED_STRATEGY_LINE_SHOWS_STAGED_FAMILY_PROGRESSION_WITHOUT_PROVING_THIRD_STEP_EXECUTION`
- candidate read:
  - controller reads should preserve the visible stepwise family progression `PERTURBATION` to `BASELINE` to `BOUNDARY_SWEEP`, while still keeping the third family as queued continuation state rather than executed run history
- why candidate:
  - this is the parent's unique sibling-specific staged-strategy seam
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:2`
  - `MANIFEST.json`

## Candidate RC5: `CLEAN_PACKET_TRANSPORT_DOES_NOT_ERASE_FAIL_CLOSED_EXHAUSTION_OR_PROMOTION_DEBT`
- candidate read:
  - controller reads should preserve that zero parked packets coexist with three `PARKED` promotion states, three unresolved blockers, and an `A2_OPERATOR_SET_EXHAUSTED` plus `SCHEMA_FAIL` stop boundary despite the preserved next-step packet
- why candidate:
  - this is the parent's narrowest controller fence for clean transport without semantic closure
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:6`
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

## Quarantined Q2: `EMPTY_A1_STRATEGIES_2_AS_A_SECOND_STRATEGY_SURFACE`
- quarantine read:
  - do not let the empty `a1_strategies 2/` directory masquerade as a second live strategy lineage
- why quarantined:
  - the real strategy packets survive only under `zip_packets/`
- parent dependencies:
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:7`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q3: `ZERO_PACKET_PARKS_AS_PROOF_OF_SEMANTIC_CLOSURE`
- quarantine read:
  - do not treat zero parked packets as proof that promotion truth has closed
- why quarantined:
  - state still preserves parked promotion outcomes and unresolved blockers
- parent dependencies:
  - `TENSION_MAP__v1.md:5`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q4: `STRATEGY_FAMILY_PROGRESSION_AS_PROOF_THAT_BOUNDARY_SWEEP_EXECUTED_SUCCESSFULLY`
- quarantine read:
  - do not let the visible `PERTURBATION -> BASELINE -> BOUNDARY_SWEEP` progression retell the queued third packet as executed success
- why quarantined:
  - the third family survives only as the preserved continuation proposal
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:2`
