---
id: "A1_CARTRIDGE::RUN_ANCHOR_AND_REGENERATION_WITNESSES"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# RUN_ANCHOR_AND_REGENERATION_WITNESSES_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::RUN_ANCHOR_AND_REGENERATION_WITNESSES`

## Description
Multi-lane adversarial examination envelope for RUN_ANCHOR_AND_REGENERATION_WITNESSES

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: run_anchor_and_regeneration_witnesses is structurally necessary because: 30 RUN_ANCHOR files: 15 RUN_ANCHOR docs (smoke/stress test anchoring for various families including entropy bookkeeping,
- **adversarial_negative**: If run_anchor_and_regeneration_witnesses is removed, the following breaks: dependency chain on run_anchor, regeneration, witness
- **success_condition**: SIM produces stable output when run_anchor_and_regeneration_witnesses is present
- **fail_condition**: SIM diverges or produces contradictory output without run_anchor_and_regeneration_witnesses
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[RUN_ANCHOR_AND_REGENERATION_WITNESSES]]

## Inward Relations
- [[RUN_ANCHOR_AND_REGENERATION_WITNESSES_COMPILED]] → **COMPILED_FROM**
