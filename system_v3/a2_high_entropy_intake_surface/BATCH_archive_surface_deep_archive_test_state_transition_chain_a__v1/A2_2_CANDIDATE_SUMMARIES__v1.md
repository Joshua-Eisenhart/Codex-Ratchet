# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_STATE_TRANSITION_CHAIN_A` is a mixed run object with two executed state transitions, one queued third A1 strategy, explicit sequence counters, and an exact duplicate ` 3` file family at the root.

## Candidate Summary B
Its strongest contradiction is count drift across layers. Summary and soak say `3`, sequence counters say `A1 3`, but canonical state and executed events preserve only `2` completed transitions; the queued `000003_A1_TO_A0_STRATEGY_ZIP.zip` is rooted on the final summary/state hash `3ce0407f...` rather than on the last visible event endpoint `232c1595...`.

## Candidate Summary C
The second executed step downshifts to `BASELINE/T0_ATOM`, records one `SCHEMA_FAIL`, and proposes both lanes at `S0002`, but final survivors keep only `S_BIND_ALPHA_ALT_ALT_S0002` while the target lane remains `S_BIND_ALPHA_S0001`; the root also carries exact duplicate primary files and runtime-path leakage inside archived event rows.
