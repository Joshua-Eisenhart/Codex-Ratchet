# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_REAL_A1_001` is a compact one-step run with one strategy packet, one export packet, one Thread-S snapshot, and two SIM evidence returns, with no retained queue continuation and no retained sequence ledger.

## Candidate Summary B
Its strongest contradiction is not transport failure but naming and closure mismatch. The run id says `TEST_REAL_A1_001`, while summary says `a1_source replay`, `needs_real_llm false`, and the final snapshot hash `d0f83cb5...` sits above the only event row’s `6835e766...`.

## Candidate Summary C
The packet layer is richer than the final bookkeeping layer. Both SIM result packets emit `NEG_NEG_BOUNDARY` kill signals and the Thread-S snapshot lists pending evidence for both retained specs, while final state keeps both `kill_log` and `evidence_pending` empty.
