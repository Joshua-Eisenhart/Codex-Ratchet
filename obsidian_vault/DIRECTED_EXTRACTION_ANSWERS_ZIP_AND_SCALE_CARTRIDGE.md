---
id: "A1_CARTRIDGE::DIRECTED_EXTRACTION_ANSWERS_ZIP_AND_SCALE"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# DIRECTED_EXTRACTION_ANSWERS_ZIP_AND_SCALE_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::DIRECTED_EXTRACTION_ANSWERS_ZIP_AND_SCALE`

## Description
Multi-lane adversarial examination envelope for DIRECTED_EXTRACTION_ANSWERS_ZIP_AND_SCALE

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: directed_extraction_answers_zip_and_scale is structurally necessary because: Directed extraction from thread context: 9 ZIP types enumerated (MEGABOOT, RATCHET_BUNDLE, FULL+, FULL++, ZIP_JOB, SIM_P
- **adversarial_negative**: If directed_extraction_answers_zip_and_scale is removed, the following breaks: dependency chain on extraction, zip_types, batch_scale
- **success_condition**: SIM produces stable output when directed_extraction_answers_zip_and_scale is present
- **fail_condition**: SIM diverges or produces contradictory output without directed_extraction_answers_zip_and_scale
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[DIRECTED_EXTRACTION_ANSWERS_ZIP_AND_SCALE]]

## Inward Relations
- [[DIRECTED_EXTRACTION_ANSWERS_ZIP_AND_SCALE_COMPILED]] → **COMPILED_FROM**
