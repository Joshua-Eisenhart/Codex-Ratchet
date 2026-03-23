---
id: "A1_CARTRIDGE::EXTRACTION_ASSERTIONS_V1"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# EXTRACTION_ASSERTIONS_V1_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::EXTRACTION_ASSERTIONS_V1`

## Description
Multi-lane adversarial examination envelope for EXTRACTION_ASSERTIONS_V1

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: extraction_assertions_v1 is structurally necessary because: Archived Work File: ASSERT 1 (Row completeness):
- **adversarial_negative**: If extraction_assertions_v1 is removed, the following breaks: dependency chain on work_archive
- **success_condition**: SIM produces stable output when extraction_assertions_v1 is present
- **fail_condition**: SIM diverges or produces contradictory output without extraction_assertions_v1
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[EXTRACTION_ASSERTIONS_V1]]

## Inward Relations
- [[EXTRACTION_ASSERTIONS_V1_COMPILED]] → **COMPILED_FROM**
