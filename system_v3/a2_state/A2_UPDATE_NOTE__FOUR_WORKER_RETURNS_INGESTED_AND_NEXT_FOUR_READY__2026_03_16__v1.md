# A2_UPDATE_NOTE__FOUR_WORKER_RETURNS_INGESTED_AND_NEXT_FOUR_READY__2026_03_16__v1

Status: `DERIVED_A2`
Date: 2026-03-16

## What changed

Ingested four worker returns into the closeout sink and staged the next four system-level worker seams.

Closeout sink state after ingest:

- `packet_count = 13`
- all current decisions are `STOP`
- all current diagnoses are `healthy_but_ready_to_stop`

## What the four returns added

1. a safe runs cleanup plan with exact already-cleared archive/quarantine candidates
2. an A2 intake bloat classification result showing cold-index prep is needed before mutation
3. core spec integration for graph subset tooling and validation provenance
4. an A2-state bloat audit showing duplicate launch artifacts and note-chain accumulation need exact candidate packing before consolidation

## Next four justified seams

1. execute only the already-cleared safe runs moves
2. patch closeout extraction so current worker closeout format ingests directly
3. produce a reusable intake cold-index prep artifact
4. produce an exact A2-state duplicate-surface candidate pack
