---
id: "A1_CARTRIDGE::CONTROL_PLANE_MANIFEST"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# CONTROL_PLANE_MANIFEST_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::CONTROL_PLANE_MANIFEST`

## Description
Multi-lane adversarial examination envelope for CONTROL_PLANE_MANIFEST

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: control_plane_manifest is structurally necessary because: MANIFEST.json (129B): [{"byte_size":53,"rel_path":"A0_SAVE_SUMMARY.json","sha256":"5abf01c2e17048d9fdc60fab0bcf716482938
- **adversarial_negative**: If control_plane_manifest is removed, the following breaks: dependency chain on control_plane, json, batch_ingest
- **success_condition**: SIM produces stable output when control_plane_manifest is present
- **fail_condition**: SIM diverges or produces contradictory output without control_plane_manifest
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[CONTROL_PLANE_MANIFEST]]

## Inward Relations
- [[CONTROL_PLANE_MANIFEST_COMPILED]] → **COMPILED_FROM**
