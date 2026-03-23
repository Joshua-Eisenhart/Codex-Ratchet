# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_root_spec_control_spine_drift_refresh__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## 1) Scope
- bounded live-source refresh over the queued active root/spec control-spine family
- purpose:
  - preserve the exact six live files that no longer match the earlier first-pass manifest
  - keep the earlier batch intact as a historical snapshot
  - record where the active owner/control/pipeline/persistence packet expanded after the first pass

## 2) Source Set
- live drifted source members:
  - `system_v3/specs/00_MANIFEST.md`
  - `system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
  - `system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
  - `system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
  - `system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
- comparison anchors:
  - `BATCH_systemv3_active_root_spec_control_spine__v1/MANIFEST.json`
  - `BATCH_systemv3_active_lineage_integrity_audit__v1/MANIFEST.json`

## 3) Why This Refresh Exists
- the queued reuse check failed because the earlier batch manifest no longer matched live repo state
- drift count:
  - changed members: `6`
  - unchanged members from the earlier family: `20`
- this packet does not replace the earlier batch
- it preserves the earlier batch as a source-bound March 9 snapshot and adds the now-live delta surface beside it

## 4) Drifted Membership By Function
- `specs/00_MANIFEST.md`
  - old snapshot: `48` lines / `2365` bytes
  - live source: `64` lines / `3508` bytes
  - main live drift:
    - tracked-baseline versus local-extension wording for items `24..29`
    - explicit active-process supplement list
    - stronger live-overlay note for missing tracked surfaces
- `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - old snapshot: `281` lines / `9959` bytes
  - live source: `303` lines / `10875` bytes
  - main live drift:
    - current live packet-profile section
    - helper summary fields `target_terms`, `family_terms`, and `admissibility`
    - explicit probe-dependency and selector-output boundary notes
- `specs/07_A2_OPERATIONS_SPEC.md`
  - old snapshot: `308` lines / `12516` bytes
  - live source: `309` lines / `12703` bytes
  - main live drift:
    - active A2 update loop
    - active audit loop
    - repo-shape classification rule
    - stronger pause-when-A2-stale operational rule
- `specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
  - old snapshot: `92` lines / `3041` bytes
  - live source: `98` lines / `3297` bytes
  - main live drift:
    - fixed run-surface subpaths
    - explicit resume-state split
    - `_CURRENT_STATE` lean-cache constraints
    - no-sprawl filesystem rule
- `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
  - old snapshot: `173` lines / `8391` bytes
  - live source: `202` lines / `9405` bytes
  - main live drift:
    - resume-state surface rules
    - regeneration witness retention
    - packet-journal compaction
    - archive demotion after anchor coverage
- `specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
  - old snapshot: `176` lines / `5343` bytes
  - live source: `200` lines / `6934` bytes
  - main live drift:
    - current live compatibility profile
    - canonical file-interface expansion
    - contradiction registry
    - fuller seal and compaction contracts
    - deterministic refresh sequence

## 5) Grouped Read
- read-order and owner/control expansion packet:
  - `00_MANIFEST.md`
  - `05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - `07_A2_OPERATIONS_SPEC.md`
- run-surface and persistence concretion packet:
  - `08_PIPELINE_AND_STATE_FLOW_SPEC.md`
  - `16_ZIP_SAVE_AND_TAPES_SPEC.md`
  - `19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`

## 6) Current Best Read
- the earlier first-pass control-spine batch remains historically useful, but it is not current on these six files
- the live active packet is now more explicit about:
  - supplement overlays and tracked-versus-local read order
  - A1 packet-shape and admissibility helper summaries
  - A2 freshness and audit loops
  - lean run-surface and resume-state layout
  - ZIP witness retention and archive-demotion discipline
  - A2 persistence compatibility and seal mechanics

## 7) Notes
- no active source was mutated
- no older batch was rewritten
- this packet is a bounded refresh surface, not a retroactive normalization of the earlier active chain
