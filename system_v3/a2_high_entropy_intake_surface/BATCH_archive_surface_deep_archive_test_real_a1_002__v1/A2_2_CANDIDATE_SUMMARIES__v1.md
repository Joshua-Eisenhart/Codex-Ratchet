# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_REAL_A1_002` is a compact two-step run with a symmetric `2/2/2/2` packet lattice, no retained `sequence_state.json`, and no queued continuation in `a1_inbox/`.

## Candidate Summary B
Its strongest contradiction is lineage and closure mismatch rather than raw transport failure. The run id says `TEST_REAL_A1_002`, summary says `a1_source replay` and `needs_real_llm false`, and the retained hash chain splits twice: from step-1 event endpoint `7a249c9e...` to step-2 input `cc9ebfe4...`, then from last event endpoint `7716a637...` to final summary/state hash `b87bc843...`.

## Candidate Summary C
The second step advances both proposal lanes to baseline `T0_ATOM` `S0002` specs and records one `SCHEMA_FAIL`, but final survivors keep only `S_SIM_ALT_OMEGA_ALT_S0002` while the `SIGMA` target remains at `S_SIM_TARGET_SIGMA_S0001`; both retained SIM packets also emit `NEG_NEG_BOUNDARY` kill signals while final state keeps `kill_log` empty.
