---
id: "A1_CARTRIDGE::ZIP_BOOT_BINDING_RULES"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# ZIP_BOOT_BINDING_RULES_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::ZIP_BOOT_BINDING_RULES`

## Description
Multi-lane adversarial examination envelope for ZIP_BOOT_BINDING_RULES

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: zip_boot_binding_rules is structurally necessary because: 5 hard rules: NO_UNBOOTED_THREADS, NO_DESKTOP_PROCEDURE_NOTES, BOOT_ROLE_MATCH, BOOT_OVERRIDES_AD_HOC_PROMPTING, CORRECT
- **adversarial_negative**: If zip_boot_binding_rules is removed, the following breaks: dependency chain on zip, boot, binding
- **success_condition**: SIM produces stable output when zip_boot_binding_rules is present
- **fail_condition**: SIM diverges or produces contradictory output without zip_boot_binding_rules
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[ZIP_BOOT_BINDING_RULES]]

## Inward Relations
- [[ZIP_BOOT_BINDING_RULES_COMPILED]] → **COMPILED_FROM**
