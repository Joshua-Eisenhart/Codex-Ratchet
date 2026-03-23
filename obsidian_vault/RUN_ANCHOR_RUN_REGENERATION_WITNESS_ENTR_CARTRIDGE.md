---
id: "A1_CARTRIDGE::RUN_ANCHOR_RUN_REGENERATION_WITNESS_ENTR"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# RUN_ANCHOR_RUN_REGENERATION_WITNESS_ENTR_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::RUN_ANCHOR_RUN_REGENERATION_WITNESS_ENTR`

## Description
Multi-lane adversarial examination envelope for RUN_ANCHOR_RUN_REGENERATION_WITNESS_ENTR

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: run_anchor_run_regeneration_witness__entr is structurally necessary because: RUN_REGENERATION_WITNESS__ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__v1.md (4986B): # RUN_REGENERATION_WITNESS__ENTROPY_BO
- **adversarial_negative**: If run_anchor_run_regeneration_witness__entr is removed, the following breaks: dependency chain on run_anchor, md, final_sweep
- **success_condition**: SIM produces stable output when run_anchor_run_regeneration_witness__entr is present
- **fail_condition**: SIM diverges or produces contradictory output without run_anchor_run_regeneration_witness__entr
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[RUN_ANCHOR_RUN_REGENERATION_WITNESS_ENTR]]

## Inward Relations
- [[RUN_ANCHOR_RUN_REGENERATION_WITNESS_ENTR_COMPILED]] → **COMPILED_FROM**
