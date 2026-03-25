# RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest current memo -> cold-core -> selector witness chain for the locally retained rescue/continuation family without keeping the full transient memo workspace

## Anchor family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`

## Why this family matters

- it is one of the highest-reuse local run families across active entropy A1/A2 doctrine
- it carries the real seeded continuation and rescue-control proof for the broad entropy route
- it also carries the current local bottleneck narrowing to `correlation_diversity_functional` / `functional`

## Preferred witness pattern

### Memo witness

- preferred family:
  - `reports/a1_external_memo_batch_driver_report.json`
- role:
  - preserves the live rescue-side memo/exchange state without keeping the full transient exchange tree

### Cold-core witness

- preferred family:
  - latest retained `a1_sandbox/cold_core/*A1_COLD_CORE_PROPOSALS_v1.json`
- role:
  - preserves the proposed-term, admissibility, and bootstrap split that the rescue family is actually operating on

### Strategy witness

- preferred family:
  - latest retained `a1_sandbox/outgoing/*A1_STRATEGY_v1__PACK_SELECTOR.json`
- role:
  - preserves selector output for the same seeded continuation family

### Phase witness

- preferred family:
  - `reports/graveyard_first_validity_wrapper_report.json`
  - or `reports/a1_exchange_serial_runner_report.json`
- role:
  - preserves the continuation-specific `path_build` / `rescue` state that distinguishes this family from a one-step executable proof

## First normalized witness instance

- instance id:
  - `ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__INSTANCE_0040`
- source run:
  - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0040`

### Normalized retained core

- memo witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0040/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - current local rescue-side driver witness with `executed_cycles_total = 355`, state `16 / 47 / 47 / 478`, and `rescue_bootstrap_stalled_terms = ["correlation_diversity_functional"]`

- cold-core witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0040/a1_sandbox/cold_core/000005_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - preserves the current narrowing where `probe_induced_partition_boundary` is clear while `correlation_diversity_functional` still carries fragment `functional`

- strategy witness:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0040/a1_sandbox/outgoing/000006_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - preserves the latest retained selector surface for the same locally retained rescue continuation branch

## Supporting control witnesses

- seeded continuation bootstrap proof:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0006/reports/a1_exchange_serial_runner_report.json`
- clean rescue novelty stall classification:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0026/reports/graveyard_first_validity_wrapper_report.json`
- rescue-target propagation proof:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0028/reports/graveyard_first_validity_wrapper_report.json`
- focus-mode proof:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0030/reports/a1_external_memo_batch_driver_report.json`
- support-only decomposition proof:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_SUPPORT_0001/a1_sandbox/cold_core/000008_A1_COLD_CORE_PROPOSALS_v1.json`

## Normalized family read

- broad cluster rescue already happened before these witnesses
- seeded continuation and later-phase rescue are locally real
- the clean rescue-side stop is `PASS__RESCUE_NOVELTY_STALLED`, not runner failure
- the current locally retained bottleneck is narrowed to `correlation_diversity_functional` / `functional`
- support-side companion flow is proven without proposal-path contamination
- preserved contradiction:
  - some downstream doctrine also paraphrases a later full-budget live-route reading for this family
  - this witness surface keeps the locally retained 0040-centered chain instead of flattening that distinction

## Local retention rule

- do not keep the full transient memo workspace for this family
- preserve only:
  - one memo witness
  - one cold-core witness
  - one strategy witness
  - a small set of phase/control witnesses
  - this provenance note

## Future refactor consequence

- once active A1/A2 surfaces cite:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`
- the raw continuation rescue runs become better candidates for archive-first handling instead of mandatory local residency
