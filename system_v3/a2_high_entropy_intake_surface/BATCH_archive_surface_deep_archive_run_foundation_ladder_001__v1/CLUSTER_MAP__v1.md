# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_ladder_001__v1`
Date: 2026-03-09

## Cluster 1: Minimal Ladder Seed
- archive meaning:
  - this object is a direct minimal run folder, not a bundle or patched export kit
- bound evidence:
  - no wrapper README
  - one-step summary and one-step event ledger
  - packet lattice contains only one strategy, one export, one B update, one save, and five SIM results
- retained interpretation:
  - useful as an early ladder seed and naming/transport baseline

## Cluster 2: Clean State With A Single Negative Scar
- archive meaning:
  - the run is clean on parked/reject dimensions but not entirely failure-free
- bound evidence:
  - `park_set_len 0`
  - `reject_log_len 0`
  - `kill_log_len 1`
  - `unresolved_promotion_blocker_count 1`
- retained interpretation:
  - preserve it as a clean one-step success that still carries one negative-signal memory

## Cluster 3: Naming Translation Residue
- archive meaning:
  - the archive preserves a translation seam between semantic action naming and protocol packet naming
- bound evidence:
  - consumed packet name `000001_FND_LR_ACTION.zip`
  - embedded packet name `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - identical bytes across both surfaces
- retained interpretation:
  - useful for historical term-lineage and demotion mapping because semantic names were later normalized into transport labels

## Cluster 4: Hash-Bound But Evidence-Light
- archive meaning:
  - the run strongly preserves final-state integrity but weakly preserves local evidence bodies
- bound evidence:
  - sidecar matches `state.json`
  - summary final hash matches state hash
  - event and soak surfaces still point to missing runtime `sim/sim_evidence_*` files
- retained interpretation:
  - archive value is strongest at the state/transport layer, weaker at the full evidence layer

