# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_nested_cache_recent_purgeable__v1`
Date: 2026-03-09

## Cluster 1: Cache Root With One Real Child
- archive meaning:
  - the nested cache root is almost empty structurally except for one `HEAT_DUMPS` carrier
- bound evidence:
  - immediate children are only `.DS_Store` and `HEAT_DUMPS`
  - nearly all bytes, files, and directories sit under `HEAT_DUMPS`
- retained interpretation:
  - useful example of a cache-labeled root collapsing into a single retained function

## Cluster 2: Timestamped Heat-Dump Rotation Hub
- archive meaning:
  - `HEAT_DUMPS` acts as a timestamped hub for thirteen rotation families
- bound evidence:
  - `13` child families spanning `20260225T004921Z` through `20260225T051154Z`
  - mix of run-surface rotations, A1-working slice, real-loop history slice, and save-export rotations
- retained interpretation:
  - useful lineage for older archive routing where recent high-entropy material was normalized into timestamped rotation buckets

## Cluster 3: Relative-Path Rotation Phase
- archive meaning:
  - the earliest rotation manifests use short relative source/destination paths
- bound evidence:
  - `RUN_SURFACE_ROTATION__20260225T004921Z`
  - `RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z`
  - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY__20260225T005437Z`
  - all point from `system_v3/runs` to `archive/...`
- retained interpretation:
  - useful early phase before manifest paths were rewritten to absolute workspace strings

## Cluster 4: Absolute-Path Mixed Rotation Phase
- archive meaning:
  - the next run-rotation wave becomes broader and switches to absolute workspace paths
- bound evidence:
  - `RUN_SURFACE_ROTATION__20260225T005815Z` moves `53` mixed run/test families while keeping two newer real-loop families
  - `RUN_SURFACE_ROTATION__20260225T010616Z` and `011409Z` repeat the same compact eight-object test/real-loop bundle
- retained interpretation:
  - useful archive read for how high-entropy material was repeatedly demoted out of the live run root while a narrow kept frontier advanced

## Cluster 5: Three Save-Export Packaging States
- archive meaning:
  - the save-export family does not preserve one stable packaging contract
- bound evidence:
  - manifested payload families: `005827Z`, `010817Z`, `011419Z`
  - manifest-only shell: `010624Z`
  - payload-only families: `012831Z`, `051154Z`
- retained interpretation:
  - useful historical contradiction showing archive export families drifting between declarative bookkeeping and detached retained payload

## Cluster 6: Late Payload-Only Run Residue
- archive meaning:
  - the latest run-rotation family preserves a real run payload after losing its outer rotation manifest
- bound evidence:
  - `RUN_SURFACE_ROTATION__20260225T050420Z` contains `RUN_REAL_LOOP_DEEP_0025`
  - `RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json` survives with hashes and `created_utc`
  - no `rotation_manifest.json` is retained at the family root
- retained interpretation:
  - useful example of rotation-wrapper loss that still leaves a full child run payload available
