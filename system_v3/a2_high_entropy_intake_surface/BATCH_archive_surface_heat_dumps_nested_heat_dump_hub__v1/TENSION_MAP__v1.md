# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_nested_heat_dump_hub__v1`
Date: 2026-03-09

## Tension 1: Heat-Dump Hub Versus Rotation Wrapper Loss
- source anchors:
  - `RUN_SURFACE_ROTATION__20260225T050420Z`
  - `SAVE_EXPORT_ROTATION__20260225T012831Z`
  - `SAVE_EXPORT_ROTATION__20260225T051154Z`
- bounded contradiction:
  - the subtree is organized around timestamped rotation wrappers, yet the latest retained families keep payload while losing the wrapper manifest
- intake handling:
  - preserve late payload-only residue as a distinct packaging state

## Tension 2: Manifest Bookkeeping Versus Missing Payload
- source anchors:
  - `SAVE_EXPORT_ROTATION__20260225T010624Z/rotation_manifest.json`
  - folder inventory for `SAVE_EXPORT_ROTATION__20260225T010624Z`
- bounded contradiction:
  - one save-export family keeps only the manifest even though it declares eight retained artifacts
- intake handling:
  - preserve this as a manifest-only shell rather than a clean empty rotation

## Tension 3: Relative Path Contract Versus Absolute Path Contract
- source anchors:
  - early run-rotation manifests `004921Z`, `005137Z`, `005437Z`
  - later run/save manifests `005815Z`, `010616Z`, `011409Z`, `005827Z`, `010624Z`, `010817Z`, `011419Z`
- bounded contradiction:
  - the same rotation hub shifts from relative archive notation to absolute workspace-path notation in the middle of one short campaign
- intake handling:
  - preserve path-format drift as historical packaging evolution

## Tension 4: Broad Sweep Versus Repeated Residual Bundle
- source anchors:
  - `RUN_SURFACE_ROTATION__20260225T005815Z`
  - `RUN_SURFACE_ROTATION__20260225T010616Z`
  - `RUN_SURFACE_ROTATION__20260225T011409Z`
- bounded contradiction:
  - one wave sweeps fifty-three heterogeneous run/test families, but the next two waves repeat a small eight-object bundle
- intake handling:
  - preserve the shift from mass demotion to repeated residual carry-forward

## Tension 5: Family Timestamp Versus Inner Payload Timestamp
- source anchors:
  - `RUN_SURFACE_ROTATION__20260225T050420Z`
  - `RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json`
- bounded contradiction:
  - the outer family timestamp is `20260225T050420Z`, but the inner child run manifest was created at `2026-02-25T01:36:45Z`
- intake handling:
  - preserve wrapper time and payload time as different clocks

## Tension 6: Heat-Dump Carrier Versus Narrow Family Semantics
- source anchors:
  - child family inventory
- bounded contradiction:
  - one subtree labeled generically as `HEAT_DUMPS` actually mixes at least four family semantics: A1-working slices, real-loop history slices, generic run rotations, and save-export rotations
- intake handling:
  - preserve mixed family semantics instead of flattening them into one type of heat dump
