# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
Date: 2026-03-09

## Tension 1: Real-A1 Naming Versus Replay Attribution
- source anchors:
  - run id
  - `summary.json`
  - `a1_inbox/`
- bounded contradiction:
  - the run is named `TEST_REAL_A1_001`, yet summary says `a1_source replay`, `needs_real_llm false`, and the inbox is empty
- intake handling:
  - preserve the naming-versus-lineage mismatch without inferring current authority from either label

## Tension 2: Final Summary Hash Versus Only Event Endpoint
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary and sidecar bind to `d0f83cb5...`, while the sole executed event ends on `6835e766...`
- intake handling:
  - preserve summary/state sidecar as the stronger final snapshot while keeping the executed event endpoint visibly distinct

## Tension 3: Missing Sequence Ledger Versus Visible Packet Lattice
- source anchors:
  - top-level run inventory
  - `zip_packets/`
- bounded contradiction:
  - the run root retains a five-packet lattice but does not retain `sequence_state.json`
- intake handling:
  - preserve the absence as a real retention gap; do not synthesize a missing sequence surface

## Tension 4: Empty State Kill Log Versus SIM Packet Kill Signals
- source anchors:
  - `state.json`
  - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- bounded contradiction:
  - both SIM evidence files emit `NEG_NEG_BOUNDARY` kill signals, while final state keeps `kill_log` empty
- intake handling:
  - preserve packet-body kill evidence without forcing it into state-level kill bookkeeping

## Tension 5: Empty `evidence_pending` Versus Snapshot Pending Evidence
- source anchors:
  - `state.json`
  - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
- bounded contradiction:
  - state reports empty `evidence_pending`, while the Thread-S snapshot lists both retained specs as pending evidence
- intake handling:
  - preserve the snapshot/state normalization split as historical residue rather than reconciling it away

## Tension 6: Zero Packet Parks Versus Two `PARKED` Promotion States
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `state.json`
- bounded contradiction:
  - summary and soak report zero parked packets, while final state marks both sim promotion outcomes as `PARKED` and keeps two unresolved blockers
- intake handling:
  - preserve the distinction between packet transport cleanliness and semantic promotion closure
