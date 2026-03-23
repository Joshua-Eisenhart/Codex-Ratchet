---
id: "A1_CARTRIDGE::ZIP_JOB_MANIFEST_REALIZED_V1_JSON"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_JOB_MANIFEST_REALIZED_V1_JSON_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_JOB_MANIFEST_REALIZED_V1_JSON`

## Description
Multi-lane adversarial examination envelope for ZIP_JOB_MANIFEST_REALIZED_V1_JSON

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_job_manifest_realized_v1_json is structurally necessary because: Unprocessed File Type (ZIP_JOB_MANIFEST_REALIZED_v1.json): { | "consumer": "A2", | "consumer_role": "A2_REFINERY_PROCESS
- **adversarial_negative**: If zip_job_manifest_realized_v1_json is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when zip_job_manifest_realized_v1_json is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_job_manifest_realized_v1_json
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_JOB_MANIFEST_REALIZED_V1_JSON]]

## Inward Relations
- [[ZIP_JOB_MANIFEST_REALIZED_V1_JSON_COMPILED]] → **COMPILED_FROM**
