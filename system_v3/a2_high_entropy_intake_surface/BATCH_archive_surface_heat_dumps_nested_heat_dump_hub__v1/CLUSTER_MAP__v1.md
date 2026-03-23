# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_nested_heat_dump_hub__v1`
Date: 2026-03-09

## Cluster 1: One Hub, Thirteen Waves
- archive meaning:
  - this subtree is a concentrated rotation hub containing thirteen timestamped demotion/export families
- bound evidence:
  - `13` direct child families
  - earliest family at `20260225T004921Z`
  - latest family at `20260225T051154Z`
- retained interpretation:
  - useful compact ledger of a single high-entropy archival campaign rather than a diffuse dump

## Cluster 2: Early Relative-Path Demotion Phase
- archive meaning:
  - the first three run families are simple demotion slices with relative source/destination paths
- bound evidence:
  - `RUN_SURFACE_ROTATION__20260225T004921Z`
  - `RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z`
  - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY__20260225T005437Z`
  - all use `system_v3/runs` and `archive/...`
- retained interpretation:
  - useful early-stage rotation contract before path strings were expanded and family contents widened

## Cluster 3: Broad Absolute-Path Sweep
- archive meaning:
  - one wave marks a qualitative jump from narrow run-only slices to a heterogeneous demotion sweep
- bound evidence:
  - `RUN_SURFACE_ROTATION__20260225T005815Z`
  - `53` moved objects
  - moved set spans realwork audits, Codex packet families, shakedowns, QIT toolkit runs, and multiple test families
- retained interpretation:
  - useful pivot point where the archive started sweeping many experimental lanes out of the live run root at once

## Cluster 4: Repeated Compact Carry-Forward Bundle
- archive meaning:
  - two later run-rotation waves preserve a repeated compact bundle instead of another broad sweep
- bound evidence:
  - `RUN_SURFACE_ROTATION__20260225T010616Z`
  - `RUN_SURFACE_ROTATION__20260225T011409Z`
  - each moves the same eight-object test/real-loop set
  - each keeps two newer `RUN_REAL_LOOP_DEEP_*` families
- retained interpretation:
  - useful example of a stabilization phase where the archive carries forward a small residual pool repeatedly

## Cluster 5: Save-Export Rotation Drift
- archive meaning:
  - the save-export family transitions from regular manifested bookkeeping into broken or partial packaging states
- bound evidence:
  - clean manifested families: `005827Z`, `010817Z`, `011419Z`
  - manifest-only shell: `010624Z`
  - payload-only families: `012831Z`, `051154Z`
- retained interpretation:
  - useful history of export packaging instability that should not be collapsed into one clean archive rule

## Cluster 6: Outer Rotation Time Versus Inner Payload Time
- archive meaning:
  - late payload-only residue preserves separate clocks for the archive wrapper and the child payload
- bound evidence:
  - outer family `RUN_SURFACE_ROTATION__20260225T050420Z`
  - inner `RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json` created at `2026-02-25T01:36:45Z`
- retained interpretation:
  - useful reminder that rotation timestamp and child run creation timestamp are distinct historical events
