# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / QUARANTINED DISTILLATES
Batch: `BATCH_work_surface_residual_handoff_and_zipjob_refinery__v1`
Extraction mode: `RESIDUAL_HANDOFF_AND_ZIPJOB_REFINERY_PASS`
Promotion status: `A2_3_REUSABLE`

## 1) Reusable Process Patterns
### `DETERMINISTIC_CONTEXT_PACK_SLIMMING`
- source anchors:
  - full/light/auto context-pack family
- distillate:
  - useful handoff pattern:
    - define one stable run order
    - preserve an explicit inventory
    - shrink the packet by deterministic seeds and one-hop references
- possible downstream consequence:
  - useful later when comparing broad context packs against leaner externally readable subsets

### `FILTER_PROCESS_HEAVY_STATE_BEFORE_EXTERNAL_HANDOFF`
- source anchors:
  - `A2_BRAIN_v1__type_counts.json`
  - `A2_BRAIN_v1__filtered__no_SYSTEM_PROCESS.json`
- distillate:
  - useful portability pattern:
    - typed state first
    - filter out `SYSTEM_PROCESS`
    - export the reduced residue rather than the full process-heavy brain
- possible downstream consequence:
  - useful later for separating durable understanding residue from runtime/process exhaust

### `STRICT_MANIFEST_TASK_ORDER_PLUS_PATH_LOCK`
- source anchors:
  - Layer-1.5 manifest
  - template v3 manifest
  - strict drop-in v7_2_4 manifest and runbook
- distillate:
  - useful ZIP_JOB hardening pattern:
    - strict task order
    - exact required outputs
    - self-audit repair
    - exact path conformance
- possible downstream consequence:
  - useful later when distinguishing early template convenience from fail-closed runnable bundles

### `EXTERNAL_HOSTILE_LANE_WITH_INTERNAL_VALIDATION`
- source anchors:
  - handoff note 25
  - refinery spec confirmation
  - violation report
- distillate:
  - useful automation pattern:
    - external claw is hostile/untrusted
    - write to quarantine first
    - validate internally
    - promote only after checks pass
- possible downstream consequence:
  - useful later for any prototype workflow that needs browser automation without granting it authority

## 2) Migration Debt / Prototype Residue
### `LIGHT_PACKS_ARE_NOT_TRULY_SELF_CONTAINED`
- read:
  - light and auto packs omit large state files and redirect them to local `audit_tmp` paths
- quarantine note:
  - the pack family is slimmer but not yet fully portable in the strong sense

### `MANIFEST_AND_OUTPUT_CONTRACT_EXPANSION_IS_STILL_MID_LADDER`
- read:
  - template v3 has `8` tasks / `16` required outputs
  - realized template expands topic-specific outputs to `30`
  - strict drop-in has `9` tasks / `21` required outputs
- quarantine note:
  - the family is stabilizing, but not yet single-shape across all artifacts

### `NAMING_AND_INTERCHANGE_DUAL_STANDARDS`
- read:
  - older topic template keeps folder-per-topic plus short leaf names
  - newer alignment reply prefers flat-file portable interchange
  - newer system doc demands long explicit path names
- quarantine note:
  - naming and interchange convergence is visible but incomplete

### `BOUNDARY_DISCIPLINE_COEXISTS_WITH_DUPLICATION_PRESSURE`
- read:
  - sandbox doctrine forbids mutation of active surfaces
  - handoff packs still duplicate large active-system doc families into `work/`
- quarantine note:
  - prototype safety is being preserved through copy/reference boundaries, not through low-volume packaging

## 3) Contradiction-Preserving Summary
- the residual refinery lane is not “just tooling cleanup”
- it is a coherent prototype logic family with several preserved splits:
  - smaller packs vs hidden local dependencies
  - small deltas vs still-broad operator cargo
  - long explicit naming vs multiple surviving interchange conventions
  - strict path/schema locks vs still-evolving manifest families
- preserving those splits is more useful than retelling the lane as finished standardization

## 4) Downstream Use Policy
- use this batch for:
  - residual Pro handoff archaeology
  - ZIP_JOB template-to-drop-in evolution
  - sandbox boundary and external-claw process patterns
  - migration-debt mapping for naming, manifest, and portability contracts
- do not use this batch for:
  - declaring any of these prototype pack families active law
  - assuming “light” means self-contained or “small” means minimal in absolute terms
  - flattening sandbox exchange notes into current runtime governance
