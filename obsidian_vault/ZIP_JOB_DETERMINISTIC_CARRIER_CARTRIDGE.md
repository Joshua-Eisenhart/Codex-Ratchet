---
id: "A1_CARTRIDGE::ZIP_JOB_DETERMINISTIC_CARRIER"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_JOB_DETERMINISTIC_CARRIER_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_JOB_DETERMINISTIC_CARRIER`

## Description
Multi-lane adversarial examination envelope for ZIP_JOB_DETERMINISTIC_CARRIER

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_job_deterministic_carrier is structurally necessary because: ZIP_JOB is the atomic deterministic inter-thread carrier. Self-describing via ZIP_JOB_MANIFEST_v1.json. Validates determ
- **adversarial_negative**: If zip_job_deterministic_carrier is removed, the following breaks: dependency chain on carrier, determinism, zip_protocol
- **success_condition**: SIM produces stable output when zip_job_deterministic_carrier is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_job_deterministic_carrier
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_JOB_DETERMINISTIC_CARRIER]]

## Inward Relations
- [[ZIP_JOB_DETERMINISTIC_CARRIER_COMPILED]] → **COMPILED_FROM**
