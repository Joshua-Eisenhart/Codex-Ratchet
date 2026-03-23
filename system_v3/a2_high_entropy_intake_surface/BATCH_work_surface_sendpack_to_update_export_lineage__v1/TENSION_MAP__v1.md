# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_sendpack_to_update_export_lineage__v1`
Extraction mode: `PACKAGED_EXPORT_LINEAGE_PASS`

## T1) one-file wrapper vs ten-child serial execution model
- source markers:
  - `work/PRO_SEND_PACK__A2_LAYER1_5__STAGE3_BATCHES_10__v1_1.zip`: `zip_listing:1-14`
- tension:
  - the Stage-3 handoff program is wrapped as a single artifact
  - the embedded set still consists of ten separate child job zips and the earlier send-order control logic
- preserved read:
  - transport compression does not erase the underlying serial execution model

## T2) outputs-only return vs broad update-pack re-expansion
- source markers:
  - `work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip`: `embedded README 1-20`
  - `work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`: `embedded MANIFEST 1-23`, `embedded MANIFEST 1121`, `embedded MANIFEST 1296`
- tension:
  - the context pack explicitly omits `system_v3` and `core_docs`
  - the later update pack restores broad `SYSTEM/core_docs` and `SYSTEM/system_v3` content
- preserved read:
  - the export family oscillates between lean return hygiene and completeness-by-bundle

## T3) tiny missing-doc delta vs 648-file update pack
- source markers:
  - `work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip`: `embedded README 1-22`
  - `work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`: `embedded MANIFEST 1-23`
- tension:
  - one pack is intentionally small and drift-avoidant
  - the next pack broadens into hundreds of copied files and nested archives
- preserved read:
  - the spillover process has not settled on one stable export scope

## T4) detached checksum sidecars vs self-describing internal manifests
- source markers:
  - all three `.sha256` sidecars: `1-1`
  - update pack embedded manifest: `1-23`
- tension:
  - the sidecars preserve only raw digests
  - the broad update pack carries a rich internal manifest with paths, bytes, and per-file hashes
- preserved read:
  - integrity is preserved at two very different descriptive levels

## T5) repair overlay says it does not replace `SYSTEM/` vs update pack ships a broad `SYSTEM/` tree
- source markers:
  - delta/update pack embedded `CANON_LOCK/00_READ_FIRST.md`: `3-5`
  - update pack embedded MANIFEST: `25-33`, `1121`, `1296`
- tension:
  - the read-first overlay insists it is not a replacement for `SYSTEM/`
  - the broad update pack still ships large `SYSTEM/core_docs` and `SYSTEM/system_v3` surfaces
- preserved read:
  - the family keeps a conceptual overlay boundary while materially sending much more than a thin overlay

## T6) curated export packaging vs bundled filename encoding damage
- source markers:
  - update pack embedded MANIFEST: `135-152`
- tension:
  - the update pack presents itself as a curated copy with file-level hashes
  - at least some imported filenames in the bundled high-entropy corpus show mojibake-style encoding damage
- preserved read:
  - curation and migration residue coexist inside the same export pack
