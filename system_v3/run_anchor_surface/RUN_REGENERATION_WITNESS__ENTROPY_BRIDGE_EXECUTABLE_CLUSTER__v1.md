# RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest current memo -> cold-core -> selector witness for the entropy executable family without preserving the full transient memo workspace

## Anchor family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`

## Why this family matters

- high doctrinal reuse across active entropy A1/A2 surfaces
- repeated dependence on wrapper, memo, cold-core, and selector artifacts from the same executable lane
- preserved contradictions matter and need one stable witness surface instead of repeated raw path blocks

## Preferred witness pattern

### Wrapper witness

- primary witness:
  - `reports/graveyard_first_validity_wrapper_report.json`
- role:
  - preserves the executed-cycle or saturation classification that doctrine repeatedly cites

### Memo witness

- primary witness:
  - `reports/a1_external_memo_batch_driver_report.json`
- role:
  - preserves the live memo/exchange state without keeping the full transient exchange tree

### Cold-core witness

- primary witness family:
  - latest retained `a1_sandbox/cold_core/*A1_COLD_CORE_PROPOSALS_v1.json`
- role:
  - preserves the path-build allowlist and admissibility state on the same executable branch

### Strategy witness

- primary witness family:
  - latest retained `a1_sandbox/outgoing/*A1_STRATEGY_v1__PACK_SELECTOR.json`
- role:
  - preserves the emitted selector-side state for the same family

## First normalized witness instance

- instance id:
  - `ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__INSTANCE_CLUSTER_CLAMP_0002`
- source run:
  - `RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002`

### Normalized retained core

- wrapper witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002/reports/graveyard_first_validity_wrapper_report.json`
  - witness meaning:
    - retained local wrapper shows `PASS__PATH_BUILD_SATURATED`, `executed_cycles = 8`, and `STOPPED__PACK_SELECTOR_FAILED` on the cleaner executable continuation

- memo witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - retained memo/exchange witness for the same executable branch and allowlist state

- cold-core witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002/a1_sandbox/cold_core/000009_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained cold-core witness showing `proposed_terms_raw = ["correlation", "correlation_polarity", "density_entropy"]` with `need_atomic_bootstrap = []`

- strategy witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002/a1_sandbox/outgoing/000008_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained selector surface for the same cluster-clamped executable branch

## Supporting control witnesses

- first executable proof:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_BROAD_0002/reports/graveyard_first_validity_wrapper_report.json`
- broad-state floor:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_BROAD_0002/state.json`
- seeded continuation saturation:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_CONT_0006/reports/graveyard_first_validity_wrapper_report.json`
- probe-companion no-advance follow-up:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_PROBE_COMPANION_0001/reports/graveyard_first_validity_wrapper_report.json`

## Normalized family read

- the first executable proof is broad `_0002`
- the cleaner active continuation is cluster-clamp `_0002`
- seeded continuation `_0006` shows local saturation under the current fence
- probe-companion `_0001` does not advance the executable floor
- preserved contradictions:
  - doctrine sometimes paraphrases cluster-clamp `_0002` as `PASS__EXECUTED_CYCLE`; the retained wrapper says `PASS__PATH_BUILD_SATURATED` with `executed_cycles = 8`
  - doctrine sometimes paraphrases probe-companion `_0001` as `PASS__EXECUTED_CYCLE` with `executed_cycles = 2`; the retained wrapper says `PASS__PATH_BUILD_SATURATED` with `executed_cycles = 0`

## Provenance rule

- the retained witness is not full replay history
- it is the minimal current chain needed to say:
  - the executable lane exists
  - the cleaner cluster-clamp continuation exists
  - cold-core proposals and selector output exist for the same branch
  - the seeded continuation is saturated rather than contaminated

## Local retention rule

- do not preserve full transient memo directories locally for this family
- preserve or distill only:
  - one wrapper witness
  - one memo witness
  - one cold-core witness
  - one strategy witness
  - a small set of support witnesses for first proof and saturation
  - this provenance note

## Future refactor consequence

- once direct local run citations are replaced broadly by:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
- the raw local executable-family runs become better archive-first candidates
