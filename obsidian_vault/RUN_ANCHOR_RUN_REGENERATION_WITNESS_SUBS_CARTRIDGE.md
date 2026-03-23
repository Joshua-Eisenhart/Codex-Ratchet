---
id: "A1_CARTRIDGE::RUN_ANCHOR_RUN_REGENERATION_WITNESS_SUBS"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# RUN_ANCHOR_RUN_REGENERATION_WITNESS_SUBS_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::RUN_ANCHOR_RUN_REGENERATION_WITNESS_SUBS`

## Description
Multi-lane adversarial examination envelope for RUN_ANCHOR_RUN_REGENERATION_WITNESS_SUBS

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: run_anchor_run_regeneration_witness__subs is structurally necessary because: RUN_REGENERATION_WITNESS__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md (3816B): # RUN_REGENERATION_WITNESS__SUBSTRATE_BASE_VALI
- **adversarial_negative**: If run_anchor_run_regeneration_witness__subs is removed, the following breaks: dependency chain on run_anchor, md, final_sweep
- **success_condition**: SIM produces stable output when run_anchor_run_regeneration_witness__subs is present
- **fail_condition**: SIM diverges or produces contradictory output without run_anchor_run_regeneration_witness__subs
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[RUN_ANCHOR_RUN_REGENERATION_WITNESS_SUBS]]

## Inward Relations
- [[RUN_ANCHOR_RUN_REGENERATION_WITNESS_SUBS_COMPILED]] → **COMPILED_FROM**
