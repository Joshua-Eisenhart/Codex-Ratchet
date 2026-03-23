# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_test_resume_001_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TEST_RESUME_001_PRESERVES_A_ZERO_WORK_EXTERNAL_HANDOFF_BOUNDARY`
- candidate read:
  - controller reads should preserve that `TEST_RESUME_001` stops at `A1_NEEDS_EXTERNAL_STRATEGY` with no accepted, parked, rejected, simulated, or survivor state, and therefore remains an outbound handoff stub rather than lower-loop work
- why candidate:
  - this is the parent's strongest execution-boundary fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC2: `DUPLICATE_STEP_1_SAVE_REQUESTS_DO_NOT_CREATE_A_HIDDEN_SECOND_STEP`
- candidate read:
  - controller reads should preserve that summary reports one step while the event ledger emits two `a1_strategy_request_emitted` rows and two save zips, without turning duplicate external request emission into evidence of a missing second step
- why candidate:
  - this is the parent's clearest event-versus-summary fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC3: `ACTIVE_RUNTIME_PACKET_PATHS_IN_ARCHIVED_EVENTS_ARE_PROVENANCE_RESIDUE_NOT_LIVE_AUTHORITY`
- candidate read:
  - controller reads should preserve the event-lane references to `system_v3/runtime/...` as leaked live-runtime provenance residue, while the preserved packet bodies now live in the archive mirror and should not be rewritten into live authority
- why candidate:
  - this is the parent's narrowest provenance-boundary fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:3`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC4: `SEQUENCE_2_IS_HEADER_DRIFT_NOT_PAYLOAD_PROGRESSION`
- candidate read:
  - controller reads should preserve that the second outbound save packet changes only `ZIP_HEADER.json` sequence while reusing the same `A0_SAVE_SUMMARY.json` and `MANIFEST.json`, so sequence advance alone does not prove progressed payload content
- why candidate:
  - this is the parent's cleanest anti-progression overread fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:2`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC5: `OUTER_RUN_HASH_AND_LEXICAL_SHELL_DO_NOT_LEGITIMIZE_INNER_SAMPLE_STRATEGY_SCAFFOLDING`
- candidate read:
  - controller reads should preserve that the run-specific outer state hash `de0e5fe9...` and retained lexical-shell surfaces wrap an inner sample strategy scaffold with `STRAT_SAMPLE_0001`, placeholder digest fields, and an all-zero inner input state hash, so the payload stays generic rather than earned
- why candidate:
  - this is the parent's strongest scaffold-versus-earned-output fence
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `CLUSTER_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:6`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q1: `TWO_OUTBOUND_SAVE_REQUESTS_AS_PROOF_OF_A_HIDDEN_SECOND_EXECUTED_STEP`
- quarantine read:
  - do not let duplicate outbound request emission rewrite the run as a two-step executed process
- why quarantined:
  - the parent preserves a one-step shell with duplicated request emission, not a retained second execution cycle
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:2`

## Quarantined Q2: `PACKET_SOURCE_AND_EXTERNAL_STRATEGY_STOP_AS_PROOF_THAT_AN_INBOUND_A1_STRATEGY_RETURNED`
- quarantine read:
  - do not infer that an inbound A1 strategy returned locally when the inbox is empty and only outbound A0-to-A1 save packets remain
- why quarantined:
  - the parent preserves an external-handoff stub, not a completed inbound-return cycle
- parent dependencies:
  - `TENSION_MAP__v1.md:5`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q3: `SEQUENCE_2_PACKET_AS_A_REAL_PAYLOAD_UPDATE`
- quarantine read:
  - do not treat the second save zip as progressed strategy content when only the header sequence changes and the payload members are reused
- why quarantined:
  - the parent explicitly preserves sequence-only header drift rather than progressed payload content
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q4: `RUN_SPECIFIC_OUTER_HASH_AS_PROOF_THAT_THE_INNER_SAMPLE_STRATEGY_IS_EARNED`
- quarantine read:
  - do not let the outer run hash and run-specific envelope legitimize the embedded sample strategy scaffold
- why quarantined:
  - the parent keeps a layered mismatch between run-specific outer metadata and generic inner payload
- parent dependencies:
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:6`
