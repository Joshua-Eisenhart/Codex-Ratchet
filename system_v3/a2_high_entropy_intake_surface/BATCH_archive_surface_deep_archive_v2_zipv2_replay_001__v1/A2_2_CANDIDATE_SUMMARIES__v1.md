# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
Date: 2026-03-09

## Candidate Summary A
`V2_ZIPV2_REPLAY_001` is a replay-authored ZIPv2 run with two executed packet cycles, one queued third strategy packet, and a final retained state that sits above the last executed event row.

## Candidate Summary B
Its strongest contradiction is closure mismatch rather than packet loss. Summary and soak both count three cycles, but the event ledger retains only two steps; the third step survives only as `000003_A1_TO_A0_STRATEGY_ZIP.zip`, rooted on the final state hash `b26e5e1d...`.

## Candidate Summary C
The second executed step records `SCHEMA_FAIL` and only partially lands. Strategy and export advance both `S0002` lanes, but final state keeps only `S_BIND_ALPHA_ALT_ALT_S0002`, while both retained SIM packets still emit `NEG_NEG_BOUNDARY` and final state keeps `kill_log` empty.
