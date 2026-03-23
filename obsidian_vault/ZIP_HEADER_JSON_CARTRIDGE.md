---
id: "A1_CARTRIDGE::ZIP_HEADER_JSON"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_HEADER_JSON_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_HEADER_JSON`

## Description
Multi-lane adversarial examination envelope for ZIP_HEADER_JSON

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_header_json is structurally necessary because: Unprocessed File Type (ZIP_HEADER.json): {"compiler_version":"A0_COMPILER_v1_PLACEHOLDER","created_utc":"1970-01-01T00:0
- **adversarial_negative**: If zip_header_json is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when zip_header_json is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_header_json
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_HEADER_JSON]]

## Inward Relations
- [[ZIP_HEADER_JSON_COMPILED]] → **COMPILED_FROM**
