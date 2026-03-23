# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_resume_001_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved Tensions
- preserve the tension that summary reports one step while the event ledger preserves two `a1_strategy_request_emitted` rows and two outbound save packets
- preserve the tension that both event rows stay at `step 1` while the second packet header advances to `sequence 2`
- preserve the tension that archived event rows reference live-runtime packet paths while the preserved packet bodies live in the archive mirror
- preserve the tension that summary, sidecar, and top-level save summary bind to `de0e5fe9...` while the embedded sample strategy input hash is all zeroes
- preserve the tension that summary says `a1_source packet` and stop reason `A1_NEEDS_EXTERNAL_STRATEGY` while no inbound A1 packet survives locally
- preserve the tension that the run-specific outer shell wraps a generic `STRAT_SAMPLE_0001` payload with placeholder hashes and fixed sample bind names
- preserve the tension that operational state is empty while lexical-shell surfaces remain populated

## Non-Smoothing Rule
- this reduction does not flatten the parent into either:
  - a real inbound-strategy return
  - or a harmless packaging-only shell with no meaningful provenance residue
- the usable controller read is narrower:
  - keep external handoff and lower-loop execution distinct
  - keep event, packet, and runtime-path residue distinct
  - keep outer run identity distinct from inner sample scaffolding
