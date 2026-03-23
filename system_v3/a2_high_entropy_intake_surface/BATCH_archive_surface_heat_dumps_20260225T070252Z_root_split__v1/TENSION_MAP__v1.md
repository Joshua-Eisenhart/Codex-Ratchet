# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_20260225T070252Z_root_split__v1`
Date: 2026-03-09

## Tension 1: One Timestamped Dump, Two Different Archive Behaviors
- source anchors:
  - `20260225T070252Z` root inventory
- bounded contradiction:
  - one branch is sandbox prompt/memo heat with flat file floods, while the other is a structured moved-out-of-git archive mirror with its own internal taxonomy
- intake handling:
  - preserve the split explicitly instead of flattening both branches into a single dump class

## Tension 2: Sandbox-Like A1 Residue Versus Normal Run Expectations
- source anchors:
  - `RUN_ENGINE_ENTROPY_0001` subtree counts and sample filenames
- bounded contradiction:
  - the branch is named like a run, but it preserves only prompt queues, lawyer memos, and consumed sandbox JSONs with no visible run-core/state spine at this level
- intake handling:
  - preserve the run-named/sandbox-shaped contradiction without inventing missing runtime surfaces

## Tension 3: Heat Dump Versus Nested Archive Mirror
- source anchors:
  - `repo_archive__moved_out_of_git`
  - `ARCHIVE_INDEX_v1.json`
- bounded contradiction:
  - the timestamped dump is supposed to be high-entropy heat, yet one entire branch is already a checkpointed archive mirror with its own recent-heat ledger
- intake handling:
  - preserve the archive-of-archives layering as lineage rather than treat it as accidental duplication

## Tension 4: Nested Archive Naming Drift
- source anchors:
  - `repo_archive__moved_out_of_git` top-level inventory
- bounded contradiction:
  - nested branch uses `OPS_LOGS` casing, keeps an empty `HEAT_DUMPS` child, and exposes `CHECKPOINTS` under low-entropy milestones, which does not match the current root naming split exactly
- intake handling:
  - preserve naming drift as historical residue instead of normalizing it into current archive taxonomy

## Tension 5: Empty Nested `HEAT_DUMPS` Versus Populated Recent-Heat Ledger
- source anchors:
  - `repo_archive__moved_out_of_git/HEAT_DUMPS`
  - `repo_archive__moved_out_of_git/ARCHIVE_INDEX_v1.json`
- bounded contradiction:
  - the nested mirror keeps an empty `HEAT_DUMPS` directory while its archive index still lists `10` recent heat-dump paths under the cache subtree
- intake handling:
  - preserve the split between empty direct child and populated indirect recent-heat references
