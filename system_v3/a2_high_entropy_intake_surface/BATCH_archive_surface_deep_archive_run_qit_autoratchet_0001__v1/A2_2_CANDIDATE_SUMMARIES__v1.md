# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0001__v1`
Date: 2026-03-09

## Candidate Summary A
This archive object is a small direct QIT autoratchet run with one consumed strategy packet, four still-active inbox packets, a restored sequence ledger, and a very small embedded packet lattice of one strategy, one export, one B update, one save, and two SIM results.

## Candidate Summary B
The strongest contradiction is accounting. `summary.json` and `soak_report.md` say the run accepted nothing, but `state.json` preserves one accepted batch and `events.jsonl` keeps a step-result row that accepted seven items before the run fell into repeated `SEQUENCE_GAP` generation failures.

## Candidate Summary C
The run is structurally clean at the packet level but semantically burdened. There are no parked or rejected packets, yet both retained sims are marked `PARKED`, one canonical evidence item remains pending, and two `NEG_INFINITE_SET` kill signals survive in state.

