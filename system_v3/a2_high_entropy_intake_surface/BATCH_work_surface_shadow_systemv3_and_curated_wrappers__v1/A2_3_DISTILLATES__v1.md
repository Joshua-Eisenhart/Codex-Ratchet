# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / QUARANTINED DISTILLATES
Batch: `BATCH_work_surface_shadow_systemv3_and_curated_wrappers__v1`
Extraction mode: `SHADOW_SYSTEMV3_DUPLICATE_AND_CURATED_WRAPPER_PASS`
Promotion status: `A2_3_REUSABLE`

## 1) Reusable Process Patterns
### `EXACT_ALIAS_TREE_DETECTION_BY_HASH`
- source anchors:
  - duplicate-surface equivalence counts inside `work/system_v3`
- distillate:
  - useful archaeology pattern:
    - compare whole subtrees by relative path and content hash
    - distinguish alias duplication from actual content evolution
- possible downstream consequence:
  - useful later when auditing shadow trees or migration residue without over-reading directory names

### `STATE_MIRROR_VS_APPEND_DRIFT`
- source anchors:
  - `a2_state`
  - `a2_persistent_context_and_memory_surface`
- distillate:
  - useful state-archaeology pattern:
    - identical core summaries can coexist with diverging append logs and sequence counters
- possible downstream consequence:
  - useful later when comparing “same state surface” claims against actual persistence drift

### `FROZEN_SUBSET_PACKAGING`
- source anchors:
  - runtime shadow comparison
  - tooling shadow comparison
  - curated wrapper readmes
- distillate:
  - useful packaging pattern:
    - freeze a subset
    - exclude many run artifacts
    - transport the subset as a thread-understanding bundle
- possible downstream consequence:
  - useful later for distinguishing a curated frozen surface from a true full-system snapshot

### `CURATED_THREAD_TRANSFER_AROUND_SHADOW_SURFACES`
- source anchors:
  - curated zips
  - control-plane bundle plaque
- distillate:
  - useful thread-transfer pattern:
    - package mechanism docs, ZIP protocols, template suites, validators, and claw tooling together for an already-informed thread
- possible downstream consequence:
  - useful later when studying how the system tried to move understanding across threads without sending the entire repo

## 2) Migration Debt / Prototype Residue
### `ALIAS_SURFACES_WITH_DIFFERENT_NAMES`
- read:
  - several duplicate subtrees differ only by directory label
- quarantine note:
  - this is clear naming-layer migration debt, not new semantics

### `AUTOWIGGLE_LIVE_VS_FROZEN_DRIFT`
- read:
  - `a1_autowiggle.py` differs between live shadow runtime and frozen runtime subset
- quarantine note:
  - the frozen runtime is not just a trimmed copy; at least one substantive file drifted

### `CURATED_WRAPPER_BLOAT_RELATIVE_TO_STATED_REDUCTION`
- read:
  - wrappers promise reduced flooding but still package broad control-plane and ZIP_JOB suites
- quarantine note:
  - the wrappers are curated, but not especially small

### `QUARANTINED_PROPOSAL_NOT_EQUAL_TO_LATER_SHADOW`
- read:
  - quarantine hashes do not match later shadow counterparts
- quarantine note:
  - the spillover tree preserved alternate proposal states rather than a clean overwrite lineage

## 3) Contradiction-Preserving Summary
- this family should not be flattened into “a backup copy of system_v3”
- it contains at least four distinct shadow behaviors:
  - exact alias duplication
  - near-live mirror drift
  - frozen subset duplication
  - curated wrapper transport
- preserving those distinctions is more valuable than retelling the tree as one uniform legacy snapshot

## 4) Downstream Use Policy
- use this batch for:
  - shadow-tree duplicate mapping
  - curated wrapper lineage
  - quarantine-vs-shadow divergence tracking
  - migration-debt analysis for alias surfaces
- do not use this batch for:
  - declaring any `work/system_v3` subtree canonical
  - assuming curated wrappers are authoritative just because they are packaged cleanly
  - collapsing shadow-tree duplication into active runtime law
