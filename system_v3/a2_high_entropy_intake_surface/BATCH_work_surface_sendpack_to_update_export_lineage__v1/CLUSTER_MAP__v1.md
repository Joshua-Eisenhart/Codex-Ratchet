# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_work_surface_sendpack_to_update_export_lineage__v1`
Extraction mode: `PACKAGED_EXPORT_LINEAGE_PASS`

## C1) `ROLLED_STAGE3_SENDPACK`
- source membership:
  - `work/PRO_SEND_PACK__A2_LAYER1_5__STAGE3_BATCHES_10__v1_1.zip`
- compressed read:
  - one wrapper zip contains the full ten-job Stage-3 send directory and its three control files
- reusable value:
  - useful repackaging pattern for collapsing a multi-file send set into one movable artifact without changing the internal job decomposition

## C2) `OUTPUTS_ONLY_THREAD_CONTEXT`
- source membership:
  - `work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip`
  - `work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip.sha256`
- compressed read:
  - a lean return pack preserves only derived outputs plus a detached digest sidecar
- reusable value:
  - strong result-hygiene pattern for returning processed artifacts without shipping the full system tree back

## C3) `MINIMAL_CANON_LOCK_DELTA`
- source membership:
  - `work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip`
  - `work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip.sha256`
- compressed read:
  - a deliberately small delta pack ships only the missing bridge docs, Playwright claw, and operator notes needed to reduce Pro-thread drift
- reusable value:
  - good minimal-update pattern for external thread repair overlays

## C4) `BROAD_SYSTEM_UPDATE_PACK`
- source membership:
  - `work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`
  - `work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip.sha256`
- compressed read:
  - the update family expands into a 648-file internal manifest plus bundles, examples, `core_docs`, and `system_v3` content
- reusable value:
  - useful full-environment export pattern when the small-delta approach is judged insufficient

## C5) `DETACHED_HASH_SIDECAR_CONVENTION`
- source membership:
  - all three `.sha256` files in `work/out/`
- compressed read:
  - integrity is preserved with one-line digest sidecars that rely on surrounding filenames rather than self-contained checksum records
- reusable value:
  - useful transport pattern, but weaker as a standalone audit artifact than a filename-bound ledger

## Cross-Cluster Read
- `C1` compresses a prior multi-file send program into one wrapper
- `C2` keeps the return path lean
- `C3` tries to preserve minimal-drift updates
- `C4` re-expands into a broad environment bundle
- `C5` keeps integrity across all three export styles while reducing checksum self-description
