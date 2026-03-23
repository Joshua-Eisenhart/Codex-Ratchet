---
id: "A1_CARTRIDGE::KNOWN_INTERNAL_INCONSISTENCIES"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# KNOWN_INTERNAL_INCONSISTENCIES_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::KNOWN_INTERNAL_INCONSISTENCIES`

## Description
Multi-lane adversarial examination envelope for KNOWN_INTERNAL_INCONSISTENCIES

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: known_internal_inconsistencies is structurally necessary because: Two recorded inconsistencies in the bootpack: (1) TERM_DRIFT appears as a rejection tag but is not in the BR-000A TAG_FE
- **adversarial_negative**: If known_internal_inconsistencies is removed, the following breaks: dependency chain on contradiction, bootpack, preserved_tension
- **success_condition**: SIM produces stable output when known_internal_inconsistencies is present
- **fail_condition**: SIM diverges or produces contradictory output without known_internal_inconsistencies
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[KNOWN_INTERNAL_INCONSISTENCIES]]

## Inward Relations
- [[KNOWN_INTERNAL_INCONSISTENCIES_COMPILED]] → **COMPILED_FROM**
