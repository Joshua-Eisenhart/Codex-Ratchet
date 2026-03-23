# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - the run preserves one executed packet loop only
  - the second retained row is a save-request handoff rather than a second executed step-result
- contradiction 2:
  - the only executed step-result ends on `3aede158...`
  - summary and state sidecar bind final closure to `5b0f04fe...` through the later request-emission row
- contradiction 3:
  - summary and soak report keep zero parked packets and zero rejects
  - final state still keeps one `PARKED` promotion outcome, one unresolved blocker, and no canonical ledger rows
- contradiction 4:
  - the retained and consumed `000001_A1_TO_A0_STRATEGY_ZIP.zip` packets share the same relative name
  - they are byte-different and semantically non-equivalent
- contradiction 5:
  - the Thread-S snapshot keeps pending evidence and the SIM packet keeps `NEG_NEG_BOUNDARY`
  - final state keeps `evidence_pending` and `kill_log` empty
- contradiction 6:
  - archived event rows still point to runtime-local paths and the run root lacks `sequence_state.json`
  - the archive still preserves a local packet lattice for the same run

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into a clean two-step execution story, a clean packet-identity story, or a clean bookkeeping story
