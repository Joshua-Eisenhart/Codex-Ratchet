# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `REQUEST_ONLY_ZIPV2_BOOTSTRAP_STAYS_AN_OUTBOUND_HANDOFF_OBJECT`
- candidate read:
  - controller reads should preserve that `V2_ZIPV2_PACKET_REQ_001` keeps only one outbound `A0_TO_A1_SAVE_ZIP` and no executed lower-loop packet cycle
- why candidate:
  - this is the parent's strongest request-only boundary
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`

## Candidate RC2: `PACKET_MODE_LABELING_DOES_NOT_IMPLY_RETAINED_INBOUND_STRATEGY`
- candidate read:
  - controller reads should preserve summary label `a1_source packet` together with zero strategy/export digests, an empty inbox, and only one outbound save packet
- why candidate:
  - this is the parent's clearest packet-label versus retained-material contradiction
- parent dependencies:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`

## Candidate RC3: `REQUESTED_THREE_STEPS_DO_NOT_OVERRIDE_ONE_RETAINED_IMMEDIATE_HANDOFF`
- candidate read:
  - controller reads should preserve `steps_requested 3` alongside `steps_completed 1`, where the only retained row is already `a1_strategy_request_emitted` with zero accepted work
- why candidate:
  - this is the parent's cleanest planning-versus-runtime residue split
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`

## Candidate RC4: `INERT_FINAL_STATE_CAN_COEXIST_WITH_POPULATED_LEXICAL_BOOTSTRAP_SHELLS`
- candidate read:
  - controller reads should preserve that accepted, survivor, SIM, evidence, and canonical-ledger counts all remain zero while `derived_only_terms`, `formula_glyph_requirements`, and `l0_lexeme_set` stay populated
- why candidate:
  - this is the parent's strongest inert-state versus preloaded-scaffold seam
- parent dependencies:
  - `state.json`
  - `state.json.sha256`

## Candidate RC5: `OUTER_SAVE_STATE_HASH_OUTRANKS_THE_EMBEDDED_ZERO_HASH_SAMPLE_STRATEGY`
- candidate read:
  - controller reads should preserve the outer save summary binding to real run hash `de0e5fe9...` while the embedded base strategy inside the only retained save packet still uses an all-zero input-state hash and placeholder self-audit digests
- why candidate:
  - this is the parent's strongest real-state versus generic-scaffold contradiction
- parent dependencies:
  - `state.json`
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`

## Candidate RC6: `RUNTIME_PATH_LEAKAGE_AND_MISSING_SEQUENCE_LEDGER_STAY_RELOCATION_RESIDUE_ONLY`
- candidate read:
  - controller reads should preserve that the archived event row still points under `system_v3/runtime/...` and the run root does not keep `sequence_state.json`, while the archive-local save packet remains the retained object for this batch
- why candidate:
  - this is the parent's cleanest relocation-era residue seam
- parent dependencies:
  - `events.jsonl`
  - `zip_packets/`
  - `MANIFEST.json`

## Quarantined Q1: `PACKET_LABEL_AS_PROOF_OF_A_COMPLETED_PACKET_LOOP`
- quarantine read:
  - do not let summary label `a1_source packet` retell the run as a completed packet loop with inbound strategy execution
- why quarantined:
  - the parent explicitly preserves an empty inbox, zero strategy/export digests, and only one outbound save packet
- parent dependencies:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`

## Quarantined Q2: `THREE_REQUESTED_STEPS_AS_HIDDEN_EXECUTED_WORK`
- quarantine read:
  - do not let the planned step count of `3` imply unretained executed work beyond the single request-emission row
- why quarantined:
  - the parent explicitly preserves one retained step and zero accepted work
- parent dependencies:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`

## Quarantined Q3: `SAVE_PACKET_SCAFFOLD_AS_EARNED_INBOUND_STRATEGY_OR_LOWER_LOOP_RESULT`
- quarantine read:
  - do not treat the embedded sample strategy in the save packet as if it were an earned returned A1 strategy or lower-loop result
- why quarantined:
  - the parent explicitly preserves it as a generic scaffold with all-zero input hash and placeholder self-audit values
- parent dependencies:
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`

## Quarantined Q4: `RUNTIME_PATHS_OR_LEXICAL_SHELLS_AS_LIVE_AUTHORITY_OR_EARNED_STATE`
- quarantine read:
  - do not promote runtime-local event paths or populated lexical shells into live authority or proof of earned lower-loop state change
- why quarantined:
  - the parent explicitly preserves relocation residue and an inert final state at the same time
- parent dependencies:
  - `events.jsonl`
  - `state.json`
