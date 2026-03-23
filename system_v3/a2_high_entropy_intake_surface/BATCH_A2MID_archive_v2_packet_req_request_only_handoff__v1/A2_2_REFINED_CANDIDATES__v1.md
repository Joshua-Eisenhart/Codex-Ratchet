# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_v2_packet_req_request_only_handoff__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `REQUEST_ONLY_ZIPV2_BOOTSTRAP_STOPS_AT_BACKWARD_A0_TO_A1_SAVE_HANDOFF`
- candidate read:
  - controller reads should preserve that `V2_ZIPV2_PACKET_REQ_001` contains one emitted backward `A0_TO_A1_SAVE_ZIP` handoff and no executed lower-loop packet cycle
- why candidate:
  - this is the parent's cleanest request-only boundary fence
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`

## Candidate RC2: `PACKET_SOURCE_LABEL_DOES_NOT_PROVE_RETAINED_INBOUND_A1_STRATEGY`
- candidate read:
  - controller reads should preserve that summary labels the run `a1_source packet` while the archive keeps zero strategy digests, an empty inbox, and only one outbound save packet
- why candidate:
  - this is the parent's strongest packet-label-versus-material contradiction
- parent dependencies:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`

## Candidate RC3: `REQUESTED_THREE_STEPS_DO_NOT_OUTRUN_SINGLE_EXTERNAL_STRATEGY_REQUEST`
- candidate read:
  - controller reads should preserve `steps_requested 3` separately from the one retained `a1_strategy_request_emitted` row with zero accepted work
- why candidate:
  - this is the parent's clearest planning-count versus retained execution fence
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`

## Candidate RC4: `REAL_OUTER_SAVE_HASH_AND_INERT_EARNED_STATE_DO_NOT_COLLAPSE_INTO_EMBEDDED_ZERO_HASH_SAMPLE_PAYLOAD`
- candidate read:
  - controller reads should preserve that the outer save summary binds to the real inert run hash `de0e5fe9...` while the embedded base strategy uses an all-zero input-state hash and placeholder self-audit digests
- why candidate:
  - this is the parent's strongest real-state-versus-sample-payload split
- parent dependencies:
  - `state.json`
  - `state.json.sha256`
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`

## Candidate RC5: `RUNTIME_PATH_LEAKAGE_AND_MISSING_SEQUENCE_LEDGER_STAY_RELOCATION_RESIDUE_ONLY`
- candidate read:
  - controller reads should preserve that archived events still point under `system_v3/runtime/...` and the run root no longer retains `sequence_state.json`, while the archive-local save packet remains the authoritative preserved artifact for this intake packet
- why candidate:
  - this is the parent's cleanest relocation-era residue fence
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/`
  - `MANIFEST.json`

## Quarantined Q1: `PACKET_MODE_LABEL_AS_PROOF_OF_COMPLETED_PACKET_LOOP`
- quarantine read:
  - do not let `a1_source packet` retell this run as a completed inbound packet loop
- why quarantined:
  - the parent explicitly preserves empty inbox, zero strategy digests, and one outbound save packet only
- parent dependencies:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`

## Quarantined Q2: `SINGLE_REQUEST_EMISSION_AS_PROOF_OF_THREE_STEP_PROGRESS`
- quarantine read:
  - do not let `steps_requested 3` imply three retained or completed steps
- why quarantined:
  - the parent explicitly preserves one immediate request-emission row and no accepted work
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`

## Quarantined Q3: `EMBEDDED_SAMPLE_SAVE_PAYLOAD_AS_EARNED_INBOUND_STRATEGY`
- quarantine read:
  - do not promote the embedded sample payload inside `000001_A0_TO_A1_SAVE_ZIP.zip` into a trusted earned strategy result
- why quarantined:
  - the parent explicitly preserves a real outer state hash above a zero-hash sample scaffold with placeholder digests
- parent dependencies:
  - `state.json`
  - `state.json.sha256`
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`

## Quarantined Q4: `RUNTIME_EVENT_PATHS_OR_MISSING_SEQUENCE_LEDGER_AS_LIVE_AUTHORITY`
- quarantine read:
  - do not treat runtime-local event paths or absent sequence bookkeeping as authority to reconstruct more execution than the archive actually preserves
- why quarantined:
  - the parent explicitly preserves relocation residue and missing sequence state at the same time
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/`
  - `MANIFEST.json`
