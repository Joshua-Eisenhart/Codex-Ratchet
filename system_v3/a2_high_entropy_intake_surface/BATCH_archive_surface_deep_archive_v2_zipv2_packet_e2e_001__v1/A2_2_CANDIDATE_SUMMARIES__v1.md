# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
Date: 2026-03-09

## Candidate Summary A
`V2_ZIPV2_PACKET_E2E_001` is a compact ZIPv2 packet-loop object with one executed strategy/export/snapshot/SIM cycle and one second-step `A0_TO_A1_SAVE_ZIP` handoff that stops on `A1_NEEDS_EXTERNAL_STRATEGY`.

## Candidate Summary B
Its strongest contradiction is packet identity drift rather than packet loss. The archive keeps a retained `000001_A1_TO_A0_STRATEGY_ZIP.zip` with typed target and alternative lanes, while the consumed copy with the same name collapses to one generic target, no alternatives, and an all-zero input state hash.

## Candidate Summary C
The packet-facing surfaces are richer than the final bookkeeping layer. The Thread-S snapshot still carries `EVIDENCE_PENDING`, the SIM packet emits `NEG_NEG_BOUNDARY`, final state keeps both `evidence_pending` and `kill_log` empty, and the final state hash is visible only through a request-emission row rather than a second executed step-result row.
