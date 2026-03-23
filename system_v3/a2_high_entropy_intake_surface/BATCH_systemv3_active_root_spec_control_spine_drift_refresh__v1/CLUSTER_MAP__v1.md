# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_root_spec_control_spine_drift_refresh__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## Cluster A: `READ_ORDER_AND_ACTIVE_OWNER_EXPANSION`
- source members:
  - `specs/00_MANIFEST.md`
  - `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - `specs/07_A2_OPERATIONS_SPEC.md`
- reusable payload:
  - clearer tracked-baseline versus local-overlay read order
  - explicit active supplement routing
  - richer A1 live packet profile and admissibility helper schema
  - stronger A2-first freshness, audit, and repo-shape classification doctrine
- quarantine note:
  - these live expansions are current source facts, but this packet does not overwrite the earlier first-pass batch or later active-lineage audit surfaces
- possible downstream consequence:
  - later active-lineage or controller-facing work should treat this cluster as the live correction surface for owner/control drift inside the original control-spine family

## Cluster B: `RUN_SURFACE_AND_PERSISTENCE_CONCRETION`
- source members:
  - `specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
  - `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
  - `specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
- reusable payload:
  - fixed run-surface subpaths and no-sprawl rules
  - lean resume-state split
  - regeneration witness retention
  - packet compaction and archive demotion rules
  - current A2 persistence compatibility profile and fuller seal contract
- quarantine note:
  - this cluster sharpens the live run/persistence shell, but it still must be compared against actual runtime and tool behavior before any authority inflation
- possible downstream consequence:
  - later runtime/tool audits should prefer this cluster over the thinner earlier snapshot when checking current save, packet, and state-layout behavior

## Cross-Cluster Couplings
- Cluster A expands the active read-order and control-memory doctrine that governs how Cluster B should be interpreted.
- Cluster B makes the filesystem and persistence consequences of Cluster A much more concrete.
- current best read:
  - the active control spine did not change everywhere
  - it thickened in two concentrated places:
    - owner/control read-order and A2/A1 operational doctrine
    - run-surface, ZIP, and persistence concretion
