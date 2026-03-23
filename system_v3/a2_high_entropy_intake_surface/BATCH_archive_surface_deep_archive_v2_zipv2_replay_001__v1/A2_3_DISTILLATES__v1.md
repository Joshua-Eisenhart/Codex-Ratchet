# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
Date: 2026-03-09

## Distillate 1
`V2_ZIPV2_REPLAY_001` preserves two executed replay steps plus one queued third strategy packet.

## Distillate 2
Summary/soak and executed events do not close cleanly: both count `3`, while the event ledger retains only steps `1` and `2`.

## Distillate 3
Two hidden hash bridges remain explicit: `8f4b8d3d... -> ac87f698...` between steps `1` and `2`, and `3f67cddc... -> b26e5e1d...` between the last event row and final retained state.

## Distillate 4
The second-step `SCHEMA_FAIL` advances only the alternative lane in final state: `S_BIND_ALPHA_ALT_ALT_S0002` survives, `S_BIND_ALPHA_S0002` does not.

## Distillate 5
Replay authorship coexists with real-LLM demand, empty inbox residue, packet-facing `NEG_NEG_BOUNDARY` kill signals, and final state that keeps `kill_log` empty.
