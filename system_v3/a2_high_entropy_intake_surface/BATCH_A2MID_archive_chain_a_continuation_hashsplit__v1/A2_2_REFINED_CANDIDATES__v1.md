# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_chain_a_continuation_hashsplit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `CHAIN_A_PRESERVES_TWO_EXECUTED_TRANSITIONS_WITH_A_QUEUED_THIRD_CONTINUATION`
- candidate read:
  - controller reads should preserve that `TEST_STATE_TRANSITION_CHAIN_A` has two executed transitions in the event ledger and canonical state, while the third step survives only as a queued `000003_A1_TO_A0_STRATEGY_ZIP.zip`
- why candidate:
  - this is the parent's strongest executed-versus-queued boundary
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
  - `A2_3_DISTILLATES__v1.md:Distillate 1`
  - `CLUSTER_MAP__v1.md:Cluster 1`

## Candidate RC2: `REPLAY_ATTRIBUTION_DOES_NOT_CANCEL_THE_RETAINED_REAL_LLM_DEMAND_FLAG`
- candidate read:
  - controller reads should preserve summary attribution `a1_source replay` together with `needs_real_llm true`, without collapsing the run into either a clean replay-only story or a clean real-LLM story
- why candidate:
  - this is the parent's clearest lineage-demand contradiction
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md:Distillate 2`
  - `MANIFEST.json`

## Candidate RC3: `THREE_STEP_COUNTING_SURFACES_DO_NOT_OVERRIDE_TWO_EXECUTED_TRANSITIONS`
- candidate read:
  - controller reads should preserve that summary, soak, and sequence counters count `3`, while canonical state and executed events preserve only `2` completed transitions
- why candidate:
  - this is the parent's cleanest count-inflation seam
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `TENSION_MAP__v1.md`
  - `sequence_state.json`
  - `events.jsonl`

## Candidate RC4: `SUMMARY_STATE_FINAL_HASH_OUTRANKS_THE_LAST_EVENT_ENDPOINT_WHILE_FEEDING_THE_QUEUED_THIRD_PACKET`
- candidate read:
  - controller reads should preserve the summary/state sidecar final hash `3ce0407f...` as the stronger final snapshot over the last executed event endpoint `232c1595...`, while also preserving that the queued third strategy packet uses that final hash as its input state
- why candidate:
  - this is the parent's narrowest closure-layer authority fence
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `MANIFEST.json`

## Candidate RC5: `SECOND_STEP_SCHEMA_FAIL_AND_BLANK_TARGET_NEGATIVE_CLASS_STAY_CORRELATED_NOT_CAUSALLY_CLOSED`
- candidate read:
  - controller reads should preserve that step 2 carries `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK` while the paired export leaves the target `NEGATIVE_CLASS` blank and the alternative retains `NEG_BOUNDARY`, without overstating that correlation into a fully proven causal mechanism
- why candidate:
  - this is the parent's narrowest fail-surface fence
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md`
  - `MANIFEST.json`

## Candidate RC6: `S0002_PROPOSAL_AND_MIXED_SURVIVOR_CARRYOVER_PREVENT_CLEAN_CHAIN_CLOSURE`
- candidate read:
  - controller reads should preserve that step 2 advances both lanes to `S0002`, but final survivors keep only `S_BIND_ALPHA_ALT_ALT_S0002` while the target lane remains `S_BIND_ALPHA_S0001`, and all retained promotion states remain `PARKED`
- why candidate:
  - this is the parent's strongest anti-closure fence
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
  - `A2_3_DISTILLATES__v1.md`
  - `state.json`
  - `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip`

## Quarantined Q1: `THREE_STEP_SUMMARY_AS_PROOF_THAT_THREE_TRANSITIONS_EXECUTED`
- quarantine read:
  - do not let summary, soak, or sequence count `3` retell the run as three executed transitions
- why quarantined:
  - the parent explicitly preserves only two executed event rows and two canonical ledger entries
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `sequence_state.json`
  - `events.jsonl`
  - `state.json`

## Quarantined Q2: `QUEUED_THIRD_STRATEGY_PACKET_AS_PROOF_OF_THIRD_STEP_SUCCESS`
- quarantine read:
  - do not let the retained third strategy packet convert a queued continuation into a completed third-step success
- why quarantined:
  - the parent explicitly preserves it as packet residue above the executed two-step spine
- parent dependencies:
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
  - `events.jsonl`

## Quarantined Q3: `EXACT_DUPLICATE_3_FILES_AS_NEW_EXECUTION_STATE`
- quarantine read:
  - do not treat the exact duplicate ` 3` file family as a newer or distinct execution surface
- why quarantined:
  - the parent explicitly marks those files as byte-identical residue
- parent dependencies:
  - `{summary 3.json,state 3.json,state.json 3.sha256,sequence_state 3.json,events 3.jsonl,soak_report 3.md}`

## Quarantined Q4: `RUNTIME_PATH_LEAKAGE_AS_PROOF_OF_LIVE_RUNTIME_AUTHORITY`
- quarantine read:
  - do not let runtime absolute paths inside archived event rows turn this archive object back into live-runtime authority
- why quarantined:
  - the parent explicitly preserves those paths as historical leakage while the packet bodies now live in the archive mirror
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/`

