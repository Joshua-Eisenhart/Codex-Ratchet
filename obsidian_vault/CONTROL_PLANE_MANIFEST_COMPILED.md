---
id: "A0_COMPILED::CONTROL_PLANE_MANIFEST"
type: "EXECUTION_BLOCK"
layer: "A0_COMPILED"
authority: "CROSS_VALIDATED"
---

# CONTROL_PLANE_MANIFEST_COMPILED
**Node ID:** `A0_COMPILED::CONTROL_PLANE_MANIFEST`

## Description
Deterministic A0 compilation of CONTROL_PLANE_MANIFEST

## Properties
- **compiled_logic**: {
  "test_target": "SIM_SPEC",
  "assertions": [
    {
      "type": "POSITIVE_STEELMAN",
      "condition": "control_plane_manifest is structurally necessary because: MANIFEST.json (129B): [{\"byte_s
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **COMPILED_FROM** → [[CONTROL_PLANE_MANIFEST_CARTRIDGE]]

## Inward Relations
- [[CONTROL_PLANE_MANIFEST_B_STATUS]] → **ADJUDICATED_FROM**
