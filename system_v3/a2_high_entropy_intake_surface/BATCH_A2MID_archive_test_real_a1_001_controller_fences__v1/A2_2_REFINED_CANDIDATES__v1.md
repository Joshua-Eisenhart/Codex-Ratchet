# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_REAL_A1_001_PRESERVES_A_ONE_STEP_PACKET_SPINE_WITH_NO_QUEUED_CONTINUATION`
- candidate read:
  - controller reads should preserve that `TEST_REAL_A1_001` has one executed packet cycle with one strategy, one export, one Thread-S snapshot, and two SIM returns, while no second-step strategy or queued continuation packet survives
- why candidate:
  - this is the parent's strongest execution-shape fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `CLUSTER_MAP__v1.md:3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC2: `REAL_A1_NAMING_DOES_NOT_OUTRANK_REPLAY_ATTRIBUTION_OR_EMPTY_INBOX_LINEAGE`
- candidate read:
  - controller reads should preserve the run-id claim `TEST_REAL_A1_001` alongside summary attribution `a1_source replay`, `needs_real_llm false`, and an empty inbox, without letting any one label retell the lineage surface by itself
- why candidate:
  - this is the parent's clearest naming-versus-lineage authority fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC3: `SUMMARY_STATE_FINAL_HASH_OUTRANKS_THE_ONLY_EVENT_ENDPOINT_AND_THE_MISSING_SEQUENCE_LEDGER_STAYS_MISSING`
- candidate read:
  - controller reads should preserve the summary/state sidecar as the stronger final snapshot over the sole event endpoint, while also preserving the missing `sequence_state.json` as a real retention gap rather than a surface to reconstruct
- why candidate:
  - this is the parent's narrowest closure-layer fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Candidate RC4: `ZERO_PACKET_PARKS_DO_NOT_ERASE_PARKED_PROMOTION_DEBT`
- candidate read:
  - controller reads should preserve that zero parked packets coexist with two `PARKED` promotion states and two unresolved blockers, so clean packet transport does not collapse into semantic closure
- why candidate:
  - this is the parent's clearest anti-clean-counter overread fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:6`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC5: `SIM_KILL_SIGNALS_AND_SNAPSHOT_PENDING_EVIDENCE_OUTRUN_FINAL_STATE_BOOKKEEPING`
- candidate read:
  - controller reads should preserve that both SIM packets retain `NEG_NEG_BOUNDARY` kill signals and the Thread-S snapshot retains pending evidence, while final state keeps both `kill_log` and `evidence_pending` empty
- why candidate:
  - this is the parent's strongest packet-body-versus-final-state bookkeeping fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:5`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q1: `REAL_A1_RUN_NAME_AS_PROOF_OF_REAL_LLM_OR_CURRENT_RUNTIME_AUTHORITY`
- quarantine read:
  - do not let the run name `TEST_REAL_A1_001` outweigh replay attribution, empty inbox lineage, and archive-only handling
- why quarantined:
  - the parent preserves a naming-versus-lineage contradiction rather than earned real-LLM authority
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `MANIFEST.json`

## Quarantined Q2: `ONE_STEP_CLEAN_TRANSPORT_AS_PROOF_OF_SEMANTIC_CLOSURE`
- quarantine read:
  - do not treat one accepted step with zero parked packets as proof that promotion truth has closed
- why quarantined:
  - state still preserves parked promotion outcomes and unresolved blockers
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:6`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q3: `MISSING_SEQUENCE_LEDGER_FILLED_IN_IMPLICITLY_FROM_THE_VISIBLE_PACKET_LATTICE`
- quarantine read:
  - do not reconstruct a missing `sequence_state.json` from the retained packet lattice as if the absent ledger still existed
- why quarantined:
  - the parent explicitly preserves the missing sequence ledger as a real retention gap
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:3`
  - `MANIFEST.json`

## Quarantined Q4: `EMPTY_STATE_KILL_LOG_AND_EVIDENCE_PENDING_AS_PROOF_THAT_SIM_RETURNS_WERE_HARMLESS_OR_FULLY_CONSUMED`
- quarantine read:
  - do not let the empty state bookkeeping fields erase the retained SIM kill signals and snapshot-level pending evidence
- why quarantined:
  - the parent keeps packet-body and snapshot evidence visibly ahead of final state aggregation
- parent dependencies:
  - `CLUSTER_MAP__v1.md:6`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:5`
