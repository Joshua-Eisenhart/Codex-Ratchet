# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
Extraction mode: `ARCHIVE_DEEP_MILESTONE_ROOT_SPLIT_PASS`

## Distillate D1
- statement:
  - the deep-archive family root splits cleanly into three top-level `system_v3` milestone zips and one overwhelmingly larger migrated run-root subtree
- source anchors:
  - family-root inventory
  - subtree counts
- possible downstream consequence:
  - later archive descent should treat the migrated subtree as the main body, not the zips

## Distillate D2
- statement:
  - `system_v3.zip` is much larger than `system_v3 3.zip` and `system_v3 2.zip`, but all three preserve the same broad `system_v3/` skeleton
- source anchors:
  - zip member counts
  - zip member listings
- possible downstream consequence:
  - useful milestone snapshot ladder for later comparison of retained system shells

## Distillate D3
- statement:
  - milestone zips in this family are not clean-room archival artifacts; they preserve `__MACOSX/*` and `.DS_Store` packaging noise
- source anchors:
  - zip member listings
- possible downstream consequence:
  - archive hygiene should not be over-inferred from milestone labeling

## Distillate D4
- statement:
  - the migrated run-root subtree is multi-campaign, not singular: foundation, qit autoratchet, signal, semantic sim, density matrix, zip tests, and resume flows all appear at the immediate run-directory layer
- source anchors:
  - immediate run subdir names
- possible downstream consequence:
  - next bounded intake should select a subtree/family inside the migrated run-root rather than reading it monolithically

## Distillate D5
- statement:
  - `_RUNS_REGISTRY.jsonl` is the smallest high-signal index into the migrated run corpus
- source anchors:
  - registry line count
  - first registry entries
- possible downstream consequence:
  - later passes should use the registry to choose bounded milestone-run batches

## Distillate D6
- statement:
  - low-entropy milestone retention here preserves both run history and current-state residue
- source anchors:
  - subtree counts
- possible downstream consequence:
  - later archive analysis should track historical-state and residue-state retention separately
