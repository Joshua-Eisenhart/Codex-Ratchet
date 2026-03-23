# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_nested_cache_recent_purgeable__v1`
Date: 2026-03-09

## Tension 1: Cache Label Versus Single-Function Reality
- source anchors:
  - nested cache root inventory
- bounded contradiction:
  - the root is named like a general recent/purgeable cache, but at this preserved boundary it effectively contains one real child only: `HEAT_DUMPS`
- intake handling:
  - preserve the cache-label versus heat-dump-carrier split directly

## Tension 2: Relative Paths Versus Absolute Paths
- source anchors:
  - early run-rotation manifests `004921Z`, `005137Z`, `005437Z`
  - later run/save manifests `005815Z`, `010616Z`, `011409Z`, `005827Z`, `010624Z`, `010817Z`, `011419Z`
- bounded contradiction:
  - the same rotation family shifts from relative `system_v3/runs -> archive/...` notation to absolute workspace paths
- intake handling:
  - preserve this as manifest-format drift, not as a semantic archive split

## Tension 3: Manifested Rotation Versus Payload-Only Residue
- source anchors:
  - `RUN_SURFACE_ROTATION__20260225T050420Z`
  - `SAVE_EXPORT_ROTATION__20260225T012831Z`
  - `SAVE_EXPORT_ROTATION__20260225T051154Z`
- bounded contradiction:
  - late families retain real payload artifacts but lose the rotation manifest that should describe them
- intake handling:
  - preserve them as payload-only residue rather than flatten them into either clean rotations or empty shells

## Tension 4: Manifest-Only Shell Versus Missing Payload
- source anchors:
  - `SAVE_EXPORT_ROTATION__20260225T010624Z/rotation_manifest.json`
  - folder inventory for `SAVE_EXPORT_ROTATION__20260225T010624Z`
- bounded contradiction:
  - the manifest declares eight kept save artifacts and zero moved artifacts, but the folder retains only the manifest file itself
- intake handling:
  - preserve this as a manifest-only shell instead of assuming the payload was never present

## Tension 5: Huge Mixed Rotation Versus Narrow Later Repeats
- source anchors:
  - `RUN_SURFACE_ROTATION__20260225T005815Z`
  - `RUN_SURFACE_ROTATION__20260225T010616Z`
  - `RUN_SURFACE_ROTATION__20260225T011409Z`
- bounded contradiction:
  - one family sweeps `53` heterogeneous run/test objects, while later families repeat a tight eight-object bundle with nearly identical contents
- intake handling:
  - preserve the shift from broad demotion sweep to repeated compact carry-forward rotations

## Tension 6: Recent Timestamp Versus Older Inner Payload Time
- source anchors:
  - `RUN_SURFACE_ROTATION__20260225T050420Z`
  - `RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json`
- bounded contradiction:
  - the outer family timestamp is `05:04:20Z`, but the retained inner run manifest was created much earlier at `01:36:45Z`
- intake handling:
  - preserve outer rotation time and inner payload creation time as separate historical clocks
