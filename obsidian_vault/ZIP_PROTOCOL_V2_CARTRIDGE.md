---
id: "A1_CARTRIDGE::ZIP_PROTOCOL_V2"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_PROTOCOL_V2_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_PROTOCOL_V2`

## Description
Multi-lane adversarial examination envelope for ZIP_PROTOCOL_V2

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_protocol_v2 is structurally necessary because: Massive 280-line protocol defining ZIP transmission. Requires ZIP_HEADER.json, MANIFEST.json, HASHES.sha256. Defines 8 z
- **adversarial_negative**: If zip_protocol_v2 is removed, the following breaks: dependency chain on transport, zip, protocol_v2
- **success_condition**: SIM produces stable output when zip_protocol_v2 is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_protocol_v2
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_PROTOCOL_V2]]

## Inward Relations
- [[ZIP_PROTOCOL_V2_COMPILED]] → **COMPILED_FROM**
