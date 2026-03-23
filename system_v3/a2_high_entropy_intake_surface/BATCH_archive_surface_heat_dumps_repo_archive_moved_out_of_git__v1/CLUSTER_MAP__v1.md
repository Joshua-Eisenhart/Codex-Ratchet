# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_repo_archive_moved_out_of_git__v1`
Date: 2026-03-09

## Cluster 1: Archive Root Inside A Later Heat Dump
- archive meaning:
  - this object is itself a coherent archive mirror nested inside a later timestamped heat dump
- bound evidence:
  - root has its own `ARCHIVE_INDEX_v1.json`
  - root splits cleanly into cache, deep archive, empty direct heat dumps, and ops logs
- retained interpretation:
  - useful archive-of-archives evidence showing one migration snapshot embedded intact in a later dump

## Cluster 2: Cache As Heat-Dump Carrier
- archive meaning:
  - the nested cache subtree is almost entirely a carrier for archived heat-dump rotations
- bound evidence:
  - `25172` files and `1154` directories live under `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
  - its only meaningful immediate child is `HEAT_DUMPS`
  - nested heat-dump families include run-surface rotations, real-loop history, A1-working slices, and save-export rotations
- retained interpretation:
  - useful lineage for how high-entropy run/save material was offloaded into rotation bundles under an earlier archive regime

## Cluster 3: Thin Deep-Archive Checkpoint Ladder
- archive meaning:
  - the nested deep archive is a milestone ladder, not a broad run corpus
- bound evidence:
  - only `CHECKPOINTS` exists directly under `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
  - exactly five `SYSTEM_V3_A1_TUNING_...` checkpoints survive
  - latest checkpoint binds to `RUN_REAL_LOOP_DEEP_0023`
- retained interpretation:
  - useful low-entropy milestone spine for early A1-tuning progression

## Cluster 4: Empty Direct HEAT_DUMPS Shell
- archive meaning:
  - the root keeps a direct `HEAT_DUMPS` child, but it is empty
- bound evidence:
  - `0` files and `0` directories in the direct child
  - `ARCHIVE_INDEX_v1.json` instead points recent heat history into `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS`
- retained interpretation:
  - useful topology seam showing that heat history was redirected into cache-hosted rotations while the older root child remained as an empty shell

## Cluster 5: Cleanup Ledger Beyond Checkpoint Time
- archive meaning:
  - cleanup maintenance continued after the last preserved deep checkpoint
- bound evidence:
  - latest checkpoint timestamp is `20260225T011355Z`
  - ops logs continue through `20260225T051102Z`
  - janitor logs delete `.DS_Store` and `__pycache__` entries under the live-era workspace paths
- retained interpretation:
  - useful evidence that archive maintenance and checkpointing were not one synchronized process

## Cluster 6: Path-Rewrite Drift Within The Mirror
- archive meaning:
  - even inside the nested mirror, path conventions were still changing midstream
- bound evidence:
  - the earliest sampled checkpoint build log writes to `/archive/CHECKPOINTS/...`
  - a later sampled checkpoint build log writes to `/archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/CHECKPOINTS/...`
  - run/save rotation manifests still use the live-era `system_v3/runs` source and `/archive/...` destination paths
- retained interpretation:
  - useful historical residue of a mirror caught during relocation and normalization rather than after it was fully stabilized
