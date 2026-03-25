# RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest memo -> cold-core -> selector witness for the first local and broad entropy-bridge pair without preserving the full transient memo workspace

## Anchor Family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1.md`

## Why This Pair Matters

- active A1/A2 doctrine repeatedly needs the first local seed proof and first broad graveyard saturation proof
- these two runs are small enough to normalize cleanly and important enough to anchor the bridge-local vs bridge-broad distinction

## First Normalized Witness Instances

### ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__LOCAL_INSTANCE_0001

- source run:
  - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_LOCAL_0001`

#### Normalized Retained Triple

- memo witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_LOCAL_0001/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - retained record that the strict local bridge seed passed through the memo/exchange stage

- cold-core witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_LOCAL_0001/a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained late local bridge proposal state for the strict local seed lane

- strategy witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_LOCAL_0001/a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained emitted strategy state for the strict local seed lane

### ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__BROAD_INSTANCE_0001

- source run:
  - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001`

#### Normalized Retained Triple

- memo witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - retained record that the broad bridge saturation lane passed through memo/exchange stage

- cold-core witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001/a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained late broad bridge proposal state for the graveyard saturation lane

- strategy witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001/a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained emitted strategy state for the broad bridge saturation lane

## Additional Report Anchors

- strict local seed wrapper:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_LOCAL_0001/reports/graveyard_first_validity_wrapper_report.json`
- broad graveyard saturation wrapper:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001/reports/graveyard_first_validity_wrapper_report.json`
- broad semantic/math gate:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001/reports/a1_semantic_and_math_substance_gate_report.json`

## Normalized Family Read

- strict local run:
  - proves one real lower-loop bridge cycle
  - remains a seed proof only

- broad run:
  - proves rich graveyard saturation and semantic/math gate passage
  - remains exploratory pressure, not closure

- regeneration continuity:
  - memo report -> cold-core proposals -> emitted strategy survive in compact retained form for both halves of the pair without preserving full transient memo trees
