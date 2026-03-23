# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_20260225T070252Z_root_split__v1`
Date: 2026-03-09

## Cluster 1: Two-Branch Timestamped Dump
- archive meaning:
  - this timestamped heat dump splits cleanly into one engine-entropy residue branch and one moved-out-of-git archive mirror
- bound evidence:
  - top-level children are only `RUN_ENGINE_ENTROPY_0001` and `repo_archive__moved_out_of_git` aside from `.DS_Store`
- retained interpretation:
  - useful archive signature for a heat dump that already separated prompt/memo residue from archive relocation state

## Cluster 2: Sandbox Prompt/Memo Heat
- archive meaning:
  - `RUN_ENGINE_ENTROPY_0001` is not shaped like a normal run root; it is a dense A1 sandbox residue family
- bound evidence:
  - only three child directories exist
  - `810` consumed JSONs
  - `810` lawyer memo JSONs
  - `938` prompt queue text files
  - role names repeat across six lens/rescuer families plus a seventh `PACK_SELECTOR` prompt role
- retained interpretation:
  - useful historical example of high-volume entropy workbench output rather than earned runtime state

## Cluster 3: Nested Archive Mirror Inside A Heat Dump
- archive meaning:
  - `repo_archive__moved_out_of_git` is already a structured archive mirror, not raw spill
- bound evidence:
  - it keeps `ARCHIVE_INDEX_v1.json`, `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`, `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`, `HEAT_DUMPS`, and `OPS_LOGS`
  - the nested cache subtree alone holds `25017` files
- retained interpretation:
  - useful archive-of-archives evidence showing that one externalization pass was itself dumped into a later heat-dump root

## Cluster 4: Nested Archive Index With Its Own Recent-Heat Ledger
- archive meaning:
  - the moved-out-of-git branch preserves checkpoint and recent-heat bookkeeping internally
- bound evidence:
  - `ARCHIVE_INDEX_v1.json` names one latest checkpoint
  - it also lists `10` recent heat-dump paths under `archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/...`
- retained interpretation:
  - useful proof that the nested archive branch already carried an explicit retrieval surface rather than just raw folders

## Cluster 5: Naming Drift Across Archive Generations
- archive meaning:
  - the moved-out-of-git branch preserves naming and casing seams from an older archive layout
- bound evidence:
  - nested top-level child is `OPS_LOGS` rather than root-level `ops_logs`
  - nested `HEAT_DUMPS` exists but is empty
  - nested low-entropy branch exposes `CHECKPOINTS` while the current root family naming differs
- retained interpretation:
  - useful historical sign that archive generations were mirrored rather than normalized into one naming regime
