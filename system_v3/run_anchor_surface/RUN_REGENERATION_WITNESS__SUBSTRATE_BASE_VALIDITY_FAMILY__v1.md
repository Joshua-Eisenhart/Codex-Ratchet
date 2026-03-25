# RUN_REGENERATION_WITNESS__SUBSTRATE_BASE_VALIDITY_FAMILY__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest memo -> cold-core -> selector witness chain for the substrate-base graveyard-validity family without keeping the full transient memo workspace

## Anchor family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md`

## Why this family matters

- this is the base proof that graveyard-first validity truly executes on the substrate lane
- active doctrine needs both the broad saturation read and the tighter concept-local read
- the concept-local run is the smallest retained same-family validity chain, while the broad run still carries the larger exploratory saturation and explicit semantic-gate proof

## First normalized witness instance

- instance id:
  - `SUBSTRATE_BASE_VALIDITY_FAMILY__INSTANCE_0002`
- source run:
  - `RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_LOCAL_0002`

### Normalized retained triple

- memo witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_LOCAL_0002/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - compact retained proof that the tighter concept-local substrate-base profile executes one graveyard-first cycle at `9 / 53 / 53 / 80`

- cold-core witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_LOCAL_0002/a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained concept-local proposal surface showing the narrowed base-family landing on:
      - `trace_one`
    with remaining atomic bootstrap on:
      - `one`

- strategy witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_LOCAL_0002/a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained selector output showing the same narrowed base-family surface:
      - `one`
      - `trace_one`

## Supporting broad saturation witnesses

- broad memo witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_0003/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - preserves the exploratory broad-fuel graveyard saturation state at `39 / 153 / 153 / 247`

- broad semantic gate witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_0003/reports/a1_semantic_and_math_substance_gate_report.json`
  - witness meaning:
    - preserves the explicit graveyard-fill semantic/math pass for the broad substrate-base proof

- broad cold-core witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_0003/a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - preserves the broader exploratory candidate set that still eventually collapses to the same `one` / `trace_one` selector surface

## Normalized family read

- graveyard-first execution is real on the substrate-base lane in both broad and concept-local profiles
- the broad run is exploratory saturation mode
- the concept-local run is the cleaner same-family validity mode
- both retained selector surfaces still collapse to:
  - `one`
  - `trace_one`
- the remaining blocker is not graveyard-first execution reality but final whole-system closure

## Local retention rule

- do not keep the full transient memo workspace for this family
- preserve only:
  - one concept-local memo witness
  - one concept-local cold-core witness
  - one concept-local strategy witness
  - a small broad saturation support set
  - this provenance note
