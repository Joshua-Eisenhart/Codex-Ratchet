# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
Date: 2026-03-09

## Distillate 1
`V2_ZIPV2_PACKET_E2E_001` preserves one executed ZIPv2 packet cycle plus one external A1 save-request handoff.

## Distillate 2
Final closure splits across surfaces: the only executed step ends on `3aede158...`, while summary and state sidecar bind to `5b0f04fe...` through the later request-emission row.

## Distillate 3
Packet transport is clean while semantic closure is not: zero parked packets coexist with one `PARKED` promotion outcome, one unresolved blocker, and `accepted_batch_count 1` with `canonical_ledger_len 0`.

## Distillate 4
The archive preserves two non-equivalent copies of `000001_A1_TO_A0_STRATEGY_ZIP.zip`: the retained packet is typed and lane-rich, while the consumed copy is generic and structurally thinner.

## Distillate 5
Thread-S and SIM residue outrun final state bookkeeping: snapshot keeps pending evidence, the SIM packet keeps `NEG_NEG_BOUNDARY`, final state keeps empty `evidence_pending` and `kill_log`, and event rows still point at `system_v3/runtime/...`.
