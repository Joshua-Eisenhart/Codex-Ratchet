---
id: "A1_CARTRIDGE::PROVENANCE"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# PROVENANCE_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::PROVENANCE`

## Description
Multi-lane adversarial examination envelope for PROVENANCE

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: provenance is structurally necessary because: Archived Work File: PROVENANCE
- **adversarial_negative**: If provenance is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when provenance is present
- **fail_condition**: SIM diverges or produces contradictory output without provenance
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[PROVENANCE]]

## Inward Relations
- [[PROVENANCE_COMPILED]] → **COMPILED_FROM**
