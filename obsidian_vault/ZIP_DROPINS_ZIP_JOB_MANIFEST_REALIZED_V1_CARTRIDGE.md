---
id: "A1_CARTRIDGE::ZIP_DROPINS_ZIP_JOB_MANIFEST_REALIZED_V1"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_DROPINS_ZIP_JOB_MANIFEST_REALIZED_V1_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_DROPINS_ZIP_JOB_MANIFEST_REALIZED_V1`

## Description
Multi-lane adversarial examination envelope for ZIP_DROPINS_ZIP_JOB_MANIFEST_REALIZED_V1

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_dropins_zip_job_manifest_realized_v1 is structurally necessary because: ZIP_JOB_MANIFEST_REALIZED_v1.json (9252B): {   "consumer": "A2",   "consumer_role": "A2_REFINERY_PROCESSOR",   "created_
- **adversarial_negative**: If zip_dropins_zip_job_manifest_realized_v1 is removed, the following breaks: dependency chain on zip_dropins, json, batch_ingest
- **success_condition**: SIM produces stable output when zip_dropins_zip_job_manifest_realized_v1 is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_dropins_zip_job_manifest_realized_v1
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_DROPINS_ZIP_JOB_MANIFEST_REALIZED_V1]]

## Inward Relations
- [[ZIP_DROPINS_ZIP_JOB_MANIFEST_REALIZED_V1_COMPILED]] → **COMPILED_FROM**
