---
id: "A1_CARTRIDGE::SIM_CATALOG_V1_3"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# SIM_CATALOG_V1_3_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::SIM_CATALOG_V1_3`

## Description
Multi-lane adversarial examination envelope for SIM_CATALOG_V1_3

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: sim_catalog_v1.3 is structurally necessary because: Archived Work File: Generated at UTC: 2026-01-30T00:00:00Z
- **adversarial_negative**: If sim_catalog_v1.3 is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when sim_catalog_v1.3 is present
- **fail_condition**: SIM diverges or produces contradictory output without sim_catalog_v1.3
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[SIM_CATALOG_V1_3]]

## Inward Relations
- [[SIM_CATALOG_V1_3_COMPILED]] → **COMPILED_FROM**
