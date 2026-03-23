# RUN_REGENERATION_WITNESS__SUBSTRATE_FAMILY__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest memo -> cold-core -> selector witness for the substrate family without preserving the full transient memo workspace

## Anchor Family

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_FAMILY__v1.md`

## Why This Family Second

- the substrate family is the cleanest non-bridge executable family
- active A1/A2 docs still cite both its first failure run and later lean proof runs
- preserved local evidence exists for:
  - memo-stage report
  - cold-core proposals
  - emitted `A1_STRATEGY_v1`

## First Normalized Witness Instance

- instance id:
  - `SUBSTRATE_FAMILY__INSTANCE_0001`
- source run:
  - `RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0001`

### Normalized Retained Triple

- memo witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_10__20260309T070854Z/RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0001/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - compact retained record that the substrate-family memo/exchange stage ran through the exchange/prepack worker path

- cold-core witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_10__20260309T070854Z/RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0001/a1_sandbox/cold_core/000001_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained cold-core proposal surface showing the first admissible substrate-family candidate bundle

- strategy witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_10__20260309T070854Z/RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0001/a1_sandbox/outgoing/000001_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained selector output showing the first substrate-family emitted strategy object

### Normalized Family Read

- executable family intent:
  - first substrate-family exchange proof
- first lower-loop failure signal:
  - the narrow family still over-pulled supporting structure at this stage
- regeneration continuity:
  - memo report -> cold-core proposals -> emitted strategy all survive in one retained instance without preserving the full transient memo workspace

## Relation To Later Lean Proof Runs

- the retained triple here is the earliest compact regeneration witness
- later proof runs:
  - `0007`
  - `0008`
  - `0010`
  - `0011`
  remain important as family-level proof and lexeme-state evidence, but are not needed to define the minimal regeneration witness chain
