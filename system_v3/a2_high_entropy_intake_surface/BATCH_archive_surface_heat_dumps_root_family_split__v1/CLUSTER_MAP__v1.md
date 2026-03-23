# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_root_family_split__v1`
Date: 2026-03-09

## Cluster 1: `HEAT_DUMPS` Is A Multi-Family Archive Surface, Not A Run Root
- archive meaning:
  - the root mixes timestamped mega-dumps, current-state rotations, oversized-run buckets, save-export kits, and a long demotion ledger
- bound evidence:
  - top-level entries split into `20260225T070252Z`, two `CURRENT_STATE_ROTATIONS`, one `RUNS_OVER_2MB` bucket, one `RUN_SAVE_EXPORTS` bucket, and `RUN_DEMOTION_BATCH_01` through `RUN_DEMOTION_BATCH_13`
- retained interpretation:
  - useful archive-level classification showing `HEAT_DUMPS` as retention infrastructure rather than executable runtime input

## Cluster 2: Recursive Archive-Of-Archives Heat
- archive meaning:
  - one heat-dump branch recursively preserves an older moved-out-of-git archive that itself contains nested heat dumps
- bound evidence:
  - `20260225T070252Z` has `27615` files and `1171` directories
  - it contains `repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/...`
- retained interpretation:
  - useful historical sign of repeated externalization and demotion cycles

## Cluster 3: Current-State Rotation Residue
- archive meaning:
  - current-state dumping preserved both an empty placeholder and one loose numbered snapshot set
- bound evidence:
  - `SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223517Z` is empty
  - `SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223534Z` keeps `47` loose `state N.json` and `sequence_state N.json` files
- retained interpretation:
  - useful archive seam between intended rotation scaffolding and actual retained payload

## Cluster 4: Size-Based And Export-Based Heat Buckets
- archive meaning:
  - some heat retention is organized by file size or save-export form rather than by doctrine lineage
- bound evidence:
  - `SYSTEM_V3__RUNS_OVER_2MB__20260224T224703Z` keeps `7` large QIT family runs
  - `SYSTEM_V3__RUN_SAVE_EXPORTS__20260224T224330Z` keeps only `2` save-export zip/sha pairs
- retained interpretation:
  - useful structural split between operational retention heuristics and doctrinal demotion logic

## Cluster 5: Demotion By Move-Only, Then Move-With-Witness-Rewrite
- archive meaning:
  - the visible March 8-9 heat-dump waves show a maturation from simple reversible demotion into doctrine-coupled archive rewrites
- bound evidence:
  - batch 01 and 02A emphasize move-only reversible demotion with keep sets
  - later batches repeatedly state `move-with-witness-rewrite`
  - later manifests require `run_anchor_surface`, regeneration-witness, and even active `a1_state` / `a2_state` archive-path rewrites
- retained interpretation:
  - useful lineage for how raw run authority was displaced by normalized anchor/witness surfaces before archival move

## Cluster 6: Family-Level Meaning Replaces Raw-Run Local Coupling
- archive meaning:
  - demotion manifests repeatedly claim that family-level doctrinal meaning was absorbed by anchor/witness surfaces before raw runs were moved
- bound evidence:
  - batches 03-13 cite anchor surfaces such as entropy-bridge, substrate-family, substrate-enrichment, entropy-structure, and packet-smoke families
  - manifests repeatedly say this is archive demotion, not deletion
- retained interpretation:
  - useful archive-level explanation for why old runs remain historically important without being current local authorities
