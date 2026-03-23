# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `ONE_EXECUTED_ZIPV2_CYCLE_STOPS_AT_EXTERNAL_A1_SAVE_REQUEST`
- candidate read:
  - controller reads should preserve that `V2_ZIPV2_PACKET_E2E_001` has one executed strategy/export/snapshot/SIM cycle and then stops by emitting an external `A0_TO_A1_SAVE_ZIP` handoff rather than a second executed step-result row
- why candidate:
  - this is the parent's strongest executed-core versus handoff boundary
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
  - `zip_packets/000002_A0_TO_A1_SAVE_ZIP.zip`

## Candidate RC2: `SAVE_REQUEST_ROW_CARRIES_FINAL_CLOSURE_ABOVE_THE_ONLY_EXECUTED_RESULT`
- candidate read:
  - controller reads should preserve the summary/state-sidecar final hash `5b0f04fe...` as the stronger retained closure over the only executed step-result endpoint `3aede158...`, with that bridge appearing only through the later `a1_strategy_request_emitted` row
- why candidate:
  - this is the parent's narrowest handoff-layer authority fence
- parent dependencies:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`

## Candidate RC3: `ZERO_PACKET_PARKS_DO_NOT_CANCEL_PARKED_PROMOTION_OR_CANONICAL_LEDGER_THINNESS`
- candidate read:
  - controller reads should preserve that summary and soak report zero parked packets and zero rejects while final state still keeps one `PARKED` promotion outcome, one unresolved blocker, and `accepted_batch_count 1` with `canonical_ledger_len 0`
- why candidate:
  - this is the parent's clearest transport-cleanliness versus semantic/bookkeeping nonclosure split
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `state.json`

## Candidate RC4: `SAME_NAME_STRATEGY_PACKET_SPLITS_BY_RETAINED_AND_CONSUMED_LANES`
- candidate read:
  - controller reads should preserve `000001_A1_TO_A0_STRATEGY_ZIP.zip` as a same-name contradiction pair:
    - the retained packet is typed, lane-rich, and tied to the real prior state hash
    - the consumed copy collapses to one generic target, no alternatives, and an all-zero input state hash
- why candidate:
  - this is the parent's strongest packet-identity contradiction
- parent dependencies:
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`

## Candidate RC5: `SNAPSHOT_PENDING_EVIDENCE_AND_SIM_KILL_SIGNAL_OUTRUN_FINAL_BOOKKEEPING`
- candidate read:
  - controller reads should preserve that the Thread-S snapshot keeps `S_BIND_ALPHA_S0001` under `EVIDENCE_PENDING` and the SIM packet emits `KILL_SIGNAL NEG_NEG_BOUNDARY` while final state keeps both `evidence_pending` and `kill_log` empty
- why candidate:
  - this is the parent's strongest packet-facing residue versus final-bookkeeping contradiction
- parent dependencies:
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `state.json`

## Candidate RC6: `RUNTIME_PATH_LEAKAGE_AND_MISSING_SEQUENCE_LEDGER_STAY_RELOCATION_RESIDUE_ONLY`
- candidate read:
  - controller reads should preserve that archived event rows still point under `system_v3/runtime/...` and the run root no longer keeps `sequence_state.json`, while the archive-local packet family is still present and authoritative for this intake packet
- why candidate:
  - this is the parent's cleanest relocation-era residue seam
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/`
  - `MANIFEST.json`

## Quarantined Q1: `A1_SAVE_REQUEST_AS_SECOND_EXECUTED_STEP_SUCCESS`
- quarantine read:
  - do not let the save-request row retell the run as if a second executed strategy result actually occurred
- why quarantined:
  - the parent explicitly preserves only one executed step-result row and one later handoff row
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/000002_A0_TO_A1_SAVE_ZIP.zip`

## Quarantined Q2: `SAME_FILENAME_AS_SAME_STRATEGY_PACKET_IDENTITY`
- quarantine read:
  - do not collapse the retained and consumed `000001_A1_TO_A0_STRATEGY_ZIP.zip` copies into one packet identity because they share a relative name
- why quarantined:
  - the parent explicitly preserves different hashes, payload richness, and input-state semantics across the two locations
- parent dependencies:
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`

## Quarantined Q3: `ZERO_PARKS_AS_PROOF_OF_SEMANTIC_CLOSURE_AND_CANONICALIZATION`
- quarantine read:
  - do not let zero parked packets convert the run into closed promotion truth or a canonically retained accepted ledger
- why quarantined:
  - the parent explicitly preserves one `PARKED` promotion outcome, one unresolved blocker, and no canonical ledger rows
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `state.json`

## Quarantined Q4: `PACKET_FACING_RESIDUE_AS_ALREADY_ABSORBED_OR_RUNTIME_PATHS_AS_LIVE_AUTHORITY`
- quarantine read:
  - do not treat snapshot pending evidence, SIM kill signal, or runtime-local event paths as if they were already absorbed into final bookkeeping or as if they restored live runtime authority
- why quarantined:
  - the parent explicitly preserves empty final bookkeeping and archive-local relocation at the same time
- parent dependencies:
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `state.json`
  - `events.jsonl`
