# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
Date: 2026-03-09

## Tension 1: Real-A1 Naming Versus Replay Attribution
- source anchors:
  - run id
  - `summary.json`
  - `a1_inbox/`
- bounded contradiction:
  - the run is named `TEST_REAL_A1_002`, yet summary says `a1_source replay`, `needs_real_llm false`, and the inbox is empty
- intake handling:
  - preserve the naming-versus-lineage mismatch without inferring current authority from either label

## Tension 2: Missing Sequence Ledger Versus Visible Two-Step Packet Lattice
- source anchors:
  - top-level run inventory
  - `zip_packets/`
- bounded contradiction:
  - the run root retains a full two-step, eight-packet lattice but does not retain `sequence_state.json`
- intake handling:
  - preserve the absence as a real retention gap; do not synthesize a missing sequence surface

## Tension 3: Step-1 Event Endpoint Versus Step-2 Input Hash
- source anchors:
  - `events.jsonl`
  - `state.json`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - step 1 ends on `7a249c9e...`, while step 2 begins from `cc9ebfe4...` in both the canonical ledger and second strategy input
- intake handling:
  - preserve the hidden bridge as archive evidence of unretained normalization between visible event rows

## Tension 4: Final Summary Hash Versus Last Event Endpoint
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary and sidecar bind to `b87bc843...`, while the last executed event ends on `7716a637...`
- intake handling:
  - preserve summary/state sidecar as the stronger final snapshot while keeping the event-lattice endpoint visibly distinct

## Tension 5: Second-Step Schema Fail Versus Blank Target `NEGATIVE_CLASS`
- source anchors:
  - step-2 row in `events.jsonl`
  - `state.json`
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- bounded contradiction:
  - the second step records `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`, and the paired export block leaves the target `NEGATIVE_CLASS` blank while the alternative still keeps `NEG_BOUNDARY`
- intake handling:
  - preserve the correlation without asserting a stronger causal mechanism than the archive proves

## Tension 6: Step-2 `S0002` Proposal Versus Mixed Final Survivor Lineage
- source anchors:
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
  - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- bounded contradiction:
  - the second-step proposal surface advances both lanes to `S0002`, but the retained final survivor set advances only `S_SIM_ALT_OMEGA_ALT_S0002`; the `SIGMA` target remains at `S_SIM_TARGET_SIGMA_S0001`
- intake handling:
  - preserve the mixed lineage rather than normalizing the target lane upward to `S0002`

## Tension 7: Empty State Kill Log And Zero Packet Parks Versus Kill Signals And `PARKED` Promotion States
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `state.json`
  - both retained `SIM_TO_A0` packets
- bounded contradiction:
  - summary and soak report zero parked packets, state keeps `3` `PARKED` promotion states and an empty `kill_log`, while both SIM evidence files emit `NEG_NEG_BOUNDARY`
- intake handling:
  - preserve the distinction between packet transport cleanliness, semantic promotion closure, and final kill aggregation
