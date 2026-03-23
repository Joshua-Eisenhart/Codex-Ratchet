# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_v2_replay_hashbridge_schemafail__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `TWO_EXECUTED_REPLAY_STEPS_STAY_SEPARATE_FROM_THE_QUEUED_THIRD_STRATEGY`
- candidate read:
  - controller reads should preserve that `V2_ZIPV2_REPLAY_001` executes only steps `1` and `2`, while step `3` survives only as retained `000003_A1_TO_A0_STRATEGY_ZIP.zip`
- why candidate:
  - this is the parent's strongest executed-versus-queued boundary
- parent dependencies:
  - `events.jsonl`
  - `summary.json`
  - `soak_report.md`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`

## Candidate RC2: `COUNT_THREE_SUMMARY_AND_SOAK_SURFACES_DO_NOT_OVERRIDE_TWO_STEP_EVENT_RETENTION`
- candidate read:
  - controller reads should preserve summary and soak counting `3` while the event ledger still retains only two executed rows
- why candidate:
  - this is the parent's clearest completed-count versus retained-execution split
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `events.jsonl`

## Candidate RC3: `HIDDEN_HASH_BRIDGES_SURVIVE_ACROSS_THE_EXECUTED_SPINE_AND_FINAL_RETAINED_STATE`
- candidate read:
  - controller reads should preserve both replay-side normalization bridges:
    - `8f4b8d3d... -> ac87f698...`
    - `3f67cddc... -> b26e5e1d...`
  while also preserving that the queued third strategy packet roots itself on final hash `b26e5e1d...`
- why candidate:
  - this is the parent's narrowest closure-layer authority seam
- parent dependencies:
  - `events.jsonl`
  - `summary.json`
  - `state.json.sha256`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`

## Candidate RC4: `REPLAY_AUTHORSHIP_DOES_NOT_CANCEL_REAL_LLM_DEMAND_OR_EMPTY_INBOX_NONCONTINUATION`
- candidate read:
  - controller reads should preserve summary label `a1_source replay` together with `needs_real_llm true`, `A2_OPERATOR_SET_EXHAUSTED`, and an empty inbox even though a queued third strategy packet is retained
- why candidate:
  - this is the parent's clearest replay-authorship versus continuation-demand contradiction
- parent dependencies:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`

## Candidate RC5: `STEP2_SCHEMA_FAIL_ADVANCES_ONLY_THE_ALTERNATIVE_S0002_LANE_IN_FINAL_STATE`
- candidate read:
  - controller reads should preserve that step 2 proposes both `S_BIND_ALPHA_S0002` and `S_BIND_ALPHA_ALT_ALT_S0002`, but final state and the second snapshot retain only the alternative lane after recorded `SCHEMA_FAIL`
- why candidate:
  - this is the parent's strongest asymmetric advancement seam
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`

## Candidate RC6: `PACKET_FACING_PENDING_EVIDENCE_AND_KILL_SIGNALS_OUTRUN_FINAL_BOOKKEEPING`
- candidate read:
  - controller reads should preserve that the first snapshot keeps pending evidence for both `S0001` specs and both retained SIM packets emit `NEG_NEG_BOUNDARY`, while final state keeps `evidence_pending` and `kill_log` empty
- why candidate:
  - this is the parent's strongest packet-facing residue versus final-bookkeeping contradiction
- parent dependencies:
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `state.json`

## Quarantined Q1: `COUNT_THREE_AS_PROOF_OF_THREE_EXECUTED_REPLAY_STEPS`
- quarantine read:
  - do not let summary or soak counts retell the run as three executed replay steps
- why quarantined:
  - the parent explicitly preserves only two executed event rows and one queued third strategy packet
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `events.jsonl`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`

## Quarantined Q2: `REPLAY_LABEL_AS_PROOF_THAT_REAL_LLM_OR_FURTHER_CONTINUATION_WAS_UNNEEDED`
- quarantine read:
  - do not let replay authorship erase `needs_real_llm true`, operator exhaustion, or the absence of retained inbox continuation
- why quarantined:
  - the parent explicitly preserves those demand and packaging seams together
- parent dependencies:
  - `summary.json`
  - `a1_inbox/`

## Quarantined Q3: `STEP2_SCHEMA_FAIL_AS_EITHER_TOTAL_FAILURE_OR_CLEAN_DUAL_LANE_SUCCESS`
- quarantine read:
  - do not flatten the second step into either full collapse or full dual-lane success
- why quarantined:
  - the parent explicitly preserves partial alternative-lane advancement only
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `state.json`

## Quarantined Q4: `PACKET_FACING_KILL_AND_EVIDENCE_RESIDUE_AS_ALREADY_ABSORBED_INTO_FINAL_STATE`
- quarantine read:
  - do not treat pending-evidence residue or `NEG_NEG_BOUNDARY` kill signals as if final state had already absorbed them
- why quarantined:
  - the parent explicitly preserves empty `evidence_pending` and `kill_log` while those richer packet-facing signals remain visible
- parent dependencies:
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `state.json`
