# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved Tensions
- preserve the tension that the run is named `TEST_REAL_A1_001` while summary attributes `a1_source` to `replay`, sets `needs_real_llm` to `false`, and the inbox is empty
- preserve the tension that summary/state sidecar bind to `d0f83cb5...` while the only executed event ends on `6835e766...`
- preserve the tension that the run root retains a five-packet lattice while `sequence_state.json` is absent
- preserve the tension that summary and soak report zero parked packets while state keeps two `PARKED` promotion states and two unresolved blockers
- preserve the tension that both SIM packets retain `NEG_NEG_BOUNDARY` kill signals while final state keeps `kill_log` empty
- preserve the tension that the Thread-S snapshot lists pending evidence for both retained specs while final state keeps `evidence_pending` empty

## Non-Smoothing Rule
- this reduction does not flatten the parent into either:
  - a true real-LLM authority run
  - or a fully closed one-step clean packet story
- the usable controller read is narrower:
  - keep naming and lineage layers distinct
  - keep final-snapshot and event-endpoint layers distinct
  - keep missing-ledger absence explicit
  - keep packet and snapshot evidence distinct from final state bookkeeping
