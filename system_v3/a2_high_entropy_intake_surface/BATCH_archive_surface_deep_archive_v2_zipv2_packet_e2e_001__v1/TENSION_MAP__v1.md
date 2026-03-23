# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
Date: 2026-03-09

## Tension 1: Final Summary Hash Versus Only Executed Event Endpoint
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - the only executed step-result row ends on `3aede158...`, while summary and sidecar bind to `5b0f04fe...`; the bridge appears only in a later `a1_strategy_request_emitted` row
- intake handling:
  - preserve executed endpoint and final handoff state as distinct archive surfaces rather than collapsing them into one step-result truth

## Tension 2: Zero Packet Parks Versus One `PARKED` Promotion Outcome
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `state.json`
- bounded contradiction:
  - summary and soak report keep zero parked and zero rejected packets, while final state keeps one `PARKED` promotion status, one unresolved blocker, and no canonical ledger rows despite `accepted_batch_count 1`
- intake handling:
  - preserve the distinction between packet transport cleanliness, semantic promotion closure, and ledger retention

## Tension 3: Snapshot Pending Evidence Versus Empty Final `evidence_pending`
- source anchors:
  - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
- bounded contradiction:
  - the Thread-S snapshot keeps `S_BIND_ALPHA_S0001` under `EVIDENCE_PENDING`, while final state keeps `evidence_pending` empty
- intake handling:
  - preserve the snapshot/state split as historical residue rather than normalizing it away

## Tension 4: SIM Kill Signal Versus Empty Final `kill_log`
- source anchors:
  - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `state.json`
- bounded contradiction:
  - the SIM packet emits `KILL_SIGNAL NEG_NEG_BOUNDARY`, while final state keeps `kill_log` empty
- intake handling:
  - preserve the kill-signal residue without forcing it into final state bookkeeping

## Tension 5: Consumed Strategy Copy Versus Retained Strategy Packet
- source anchors:
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - the consumed copy is byte-different and semantically thinner than the retained packet even though both carry the same relative name
- intake handling:
  - preserve both packet forms and explicitly treat them as a contradiction pair rather than interchangeable duplicates

## Tension 6: Archive-Local Packet Family Versus Runtime-Local Event Paths
- source anchors:
  - `events.jsonl`
  - archive-local `zip_packets/`
  - missing `sequence_state.json`
- bounded contradiction:
  - the archive keeps local packet copies, but event rows still reference `system_v3/runtime/...` paths and the run root no longer retains local sequence counters
- intake handling:
  - preserve path leakage and sequence-gap residue as a relocation artifact, not as an error to repair inside the intake batch
