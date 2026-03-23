# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_repo_archive_moved_out_of_git__v1`
Date: 2026-03-09

## Tension 1: Nested Mirror Versus Current Authority
- source anchors:
  - root inventory
  - `ARCHIVE_INDEX_v1.json`
  - rotation manifests
- bounded contradiction:
  - this object is a self-consistent archive root, but it survives only as a mirror inside a later heat dump and must not be treated as current authority
- intake handling:
  - preserve it as historical archive lineage only

## Tension 2: Empty Direct HEAT_DUMPS Versus Populated Recent-Heat Ledger
- source anchors:
  - direct `HEAT_DUMPS` child
  - `ARCHIVE_INDEX_v1.json`
- bounded contradiction:
  - the direct root `HEAT_DUMPS` child is empty, yet the archive index lists ten recent heat dumps under the nested cache subtree
- intake handling:
  - preserve the direct-child emptiness and indirect heat-history population together instead of normalizing them away

## Tension 3: Checkpoint Spine Versus Later Cleanup History
- source anchors:
  - latest checkpoint `SYSTEM_V3_A1_TUNING_20260225T011355Z`
  - ops log `CLEANUP_BOOKKEEPING__20260225T051102Z.json`
- bounded contradiction:
  - the deep archive says the latest low-entropy milestone is `01:13:55Z`, but cleanup logs continue almost four hours later
- intake handling:
  - preserve checkpoint and janitor histories as asynchronous layers rather than one unified timeline

## Tension 4: Archive Mirror Versus Live Absolute Paths
- source anchors:
  - run rotation manifest
  - save-export rotation manifest
  - cleanup bookkeeping logs
- bounded contradiction:
  - the object sits under a nested heat-dump mirror, but its manifests and cleanup logs still speak in old live absolute paths under `/Users/joshuaeisenhart/Desktop/Codex Ratchet/archive/...` and `system_v3/...`
- intake handling:
  - preserve these live-era path references as historical relocation residue

## Tension 5: Stable Root Taxonomy Versus Internal Path Rewrite Drift
- source anchors:
  - early checkpoint `bootstrap_build.log`
  - later checkpoint `bootstrap_build.log`
- bounded contradiction:
  - the mirror looks structurally stable at the root, but checkpoint build logs still shift from `/archive/CHECKPOINTS/...` to `/archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/CHECKPOINTS/...`
- intake handling:
  - preserve the within-mirror path rewrite seam instead of pretending the archive was born fully normalized

## Tension 6: Cache Label Versus Heat-Dump Monoculture
- source anchors:
  - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE` inventory
- bounded contradiction:
  - the subtree is labeled as a general recent cache, but its immediate content collapses almost entirely to a single `HEAT_DUMPS` carrier
- intake handling:
  - preserve the cache-name versus heat-dump monoculture split as part of older archive semantics
