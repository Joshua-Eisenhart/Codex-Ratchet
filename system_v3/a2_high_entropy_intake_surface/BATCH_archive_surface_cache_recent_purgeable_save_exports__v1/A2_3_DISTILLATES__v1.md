# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
Extraction mode: `ARCHIVE_CACHE_SAVE_EXPORT_PASS`

## Distillate D1
- statement:
  - this archive item is a cache-tier save-export family with `5` zips, `5` detached checksum sidecars, and one explicit safe-delete marker
- source anchors:
  - family inventory
  - safe-delete file
- possible downstream consequence:
  - useful historical witness of what the system treated as recent/high-entropy/purgeable

## Distillate D2
- statement:
  - the family splits cleanly into `bootstrap` exports with no run ids and `debug` exports scoped to one autoratchet debug run identity
- source anchors:
  - embedded save-profile manifests
- possible downstream consequence:
  - later archive reduction can trace save-export lineage by profile and run-scope rather than by filename alone

## Distillate D3
- statement:
  - bootstrap and debug smoke variants are not byte-identical to their timestamped counterparts even when they preserve nearly the same corpus
- source anchors:
  - zip hash comparison
  - common-file diff results
- possible downstream consequence:
  - smoke naming in this family marks packaging/state drift, not exact duplication

## Distillate D4
- statement:
  - the most meaningful internal drift is concentrated in workspace layout and current-run/current-state files, not in broad corpus membership
- source anchors:
  - cross-zip common-file comparisons
- possible downstream consequence:
  - useful historical clue that these exports were snapshots of evolving runtime state around a mostly stable corpus

## Distillate D5
- statement:
  - even purgeable cache exports retained fuller save-state bodies and sidecars than the later top-layer archive extraction packages
- source anchors:
  - internal zip member listings
  - earlier archive packaged batch lineage
- possible downstream consequence:
  - important lineage marker for export-body loss across later archival distillation

## Distillate D6
- statement:
  - detached `.sha256` sidecars matched every export exactly
- source anchors:
  - sidecar contents
  - recomputed zip hashes
- possible downstream consequence:
  - useful minimal-integrity witness for the purgeable cache tier
