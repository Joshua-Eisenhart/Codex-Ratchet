# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_STATE_TRANSITION_CHAIN_A_PRESERVES_TWO_EXECUTED_TRANSITIONS_WITH_A_QUEUED_THIRD_STRATEGY`
- candidate read:
  - controller reads should preserve that `TEST_STATE_TRANSITION_CHAIN_A` has two executed state transitions while the third A1 step survives only as queued continuation residue in `000003_A1_TO_A0_STRATEGY_ZIP.zip`
- why candidate:
  - this is the parent's strongest executed-versus-queued boundary
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC2: `REPLAY_ATTRIBUTION_DOES_NOT_ERASE_NEEDS_REAL_LLM_TRUE`
- candidate read:
  - controller reads should preserve the summary contradiction that this run is replay-attributed while still marked `needs_real_llm true`, without forcing it into a single lineage category
- why candidate:
  - this is the parent's clearest lineage-classification fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `MANIFEST.json`

## Candidate RC3: `THREE_COUNTED_A1_STEPS_AND_FINAL_HASH_FEED_DO_NOT_MASQUERADE_AS_THREE_EXECUTED_TRANSITIONS`
- candidate read:
  - controller reads should preserve that summary, soak, and sequence counters reach `3`, and the final summary/state hash `3ce0407f...` feeds the queued third strategy, while canonical state and executed events still stop at two completed transitions
- why candidate:
  - this is the parent's narrowest count-layer and closure-layer fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC4: `SECOND_STEP_SCHEMA_FAIL_AND_BLANK_TARGET_NEGATIVE_CLASS_STAY_CORRELATED_WITHOUT_STRONGER_CAUSAL_CLAIM`
- candidate read:
  - controller reads should preserve the step-2 `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK` record together with the paired blank target `NEGATIVE_CLASS` in the second export packet, while not overstating the archive into a proven single-cause story
- why candidate:
  - this is the parent's sharpest controller-facing causal-boundary fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:6`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC5: `STEP_2_S0002_PROPOSAL_DOES_NOT_PROVE_CLEAN_TARGET_ADVANCEMENT_OR_ARCHIVE_LOCAL_CLOSURE`
- candidate read:
  - controller reads should preserve that the second-step proposal advances both lanes to `S0002`, but final survivors advance only `S_BIND_ALPHA_ALT_ALT_S0002` while the target lane remains `S_BIND_ALPHA_S0001`, and the root’s exact duplicate ` 3` files plus runtime-path leakage remain residue rather than a second branch or clean archive-local normalization
- why candidate:
  - this is the parent's strongest anti-clean-advancement and anti-second-branch overread fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `CLUSTER_MAP__v1.md:6`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:8`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q1: `THREE_COUNTED_STEPS_AS_PROOF_THAT_STEP_THREE_EXECUTED`
- quarantine read:
  - do not let summary, soak, or sequence counters rewrite the run as a three-step executed process
- why quarantined:
  - the parent preserves only two executed transitions and one queued third strategy packet
- parent dependencies:
  - `TENSION_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Quarantined Q2: `REPLAY_ATTRIBUTION_OR_NEEDS_REAL_LLM_TRUE_AS_A_SINGLE_DISPOSITIVE_LINEAGE_LABEL`
- quarantine read:
  - do not collapse the run into either fully replay-only or fully live-LLM status from one summary field
- why quarantined:
  - the parent explicitly preserves both fields together as a contradiction
- parent dependencies:
  - `TENSION_MAP__v1.md:1`
  - `MANIFEST.json`

## Quarantined Q3: `EXACT_DUPLICATE_3_FILE_FAMILY_AS_PROOF_OF_A_SECOND_RUNTIME_BRANCH`
- quarantine read:
  - do not treat the byte-identical ` 3` file family as evidence of a distinct branch
- why quarantined:
  - the parent preserves the suffixed family as exact duplicate packaging residue
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:7`

## Quarantined Q4: `RUNTIME_PATH_LEAKAGE_AS_CURRENT_PACKET_AUTHORITY`
- quarantine read:
  - do not let runtime-style packet paths inside archived events outrank the archive-local packet bodies now preserved
- why quarantined:
  - the parent preserves runtime-path leakage as provenance residue rather than live authority
- parent dependencies:
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:8`
