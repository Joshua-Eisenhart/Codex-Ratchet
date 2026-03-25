# RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest memo -> cold-core -> selector witness for the entropy-rate family without preserving the full transient memo workspace

## Anchor Family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`

## Why This Family Third

- this is the cleanest passenger-lift family after the executable bridge and substrate families
- active A1/A2 docs repeatedly need its role judgment:
  - `correlation_polarity` leads
  - `entropy_production_rate` does not
- active A1/A2 docs also reuse its thin local controls:
  - bookkeeping-pair local remains too thin
  - isolated `correlation_polarity` local remains memo-path thin
- preserved local evidence exists for:
  - memo-stage report
  - cold-core proposals
  - emitted `A1_STRATEGY_v1`

## First Normalized Witness Instance

- instance id:
  - `ENTROPY_RATE_FAMILY__INSTANCE_0001`
- source run:
  - `RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001`

### Normalized Retained Triple

- memo witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - compact retained record that the entropy-rate family ran through the memo/exchange step on the local validity lane

- cold-core witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001/a1_sandbox/cold_core/000002_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained cold-core proposal surface showing the passenger-lift family with rate, polarity, and witness-floor structure

- strategy witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001/a1_sandbox/outgoing/000001_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained selector output showing `correlation_polarity` as head and `entropy_production_rate` as `PASSENGER_ONLY`

### Normalized Family Read

- executable head:
  - `correlation_polarity`
- late passenger:
  - `entropy_production_rate`
- witness-only / support floor:
  - `density_entropy`
  - `correlation`
  - `information_work_extraction_bound`
  - `erasure_channel_entropy_cost_lower_bound`
- regeneration continuity:
  - memo report -> cold-core proposals -> emitted strategy all survive in one retained instance without preserving the full transient memo workspace

## Supporting Control Witnesses

- bookkeeping-pair local memo witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BOOKKEEPING_PAIR_LOCAL_0001/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - preserves the thin local bookkeeping state at `3 / 0 / 0 / 3` while showing the two-term pair still formed

- bookkeeping-pair local cold-core witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BOOKKEEPING_PAIR_LOCAL_0001/a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - preserves the narrow bookkeeping pair:
      - `entropy_production_rate`
      - `erasure_channel_entropy_cost_lower_bound`
    - plus the remaining atomic bootstrap debt on:
      - `cost`
      - `erasure`
      - `production`
      - `rate`

- bookkeeping-pair local strategy witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BOOKKEEPING_PAIR_LOCAL_0001/a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - preserves the thin selector outcome where the route still rides:
      - `erasure`
      - `cost`
      - `erasure_channel_entropy_cost_lower_bound`

- thin local correlation-head wrapper witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_CORRELATION_POLARITY_LOCAL_0003/reports/graveyard_first_validity_wrapper_report.json`
  - witness meaning:
    - preserves the `FAIL__SUBPROCESS` / `WAITING_FOR_MEMOS` boundary for isolated `correlation_polarity`

- thin local correlation-head cold-core witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_CORRELATION_POLARITY_LOCAL_0003/a1_sandbox/cold_core/000002_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - preserves the atomic ladder:
      - `correlation`
      - `polarity`
      - `correlation_polarity`

- thin local correlation-head strategy witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_CORRELATION_POLARITY_LOCAL_0003/a1_sandbox/outgoing/000002_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - preserves the same local selector shape even though the lane never escapes memo wait

## Preserved Read

- local bookkeeping and local `correlation_polarity` controls remain negative evidence, not promotion evidence
- preserved doctrine mismatch:
  - some downstream docs paraphrase the bookkeeping-pair local run as “no executed cycle”
  - the retained wrapper and memo surfaces record one executed cycle with no graveyard pressure
- the family-level role judgment still comes from:
  - the retained local rate witness triple
  - plus the broad executable lift proof

## Relation To Broad Rate-Lift Evidence

- the retained triple here is the compact local regeneration witness
- the broad executable lift run:
  - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RATE_LIFT_BROAD_0001`
  remains important as evidence that `entropy_production_rate` can survive in broad executable mode
- it does not overturn the local role judgment recorded here
