---
id: "A1_CARTRIDGE::A2_VS_A1_ROLE_SPLIT_FENCE"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# A2_VS_A1_ROLE_SPLIT_FENCE_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::A2_VS_A1_ROLE_SPLIT_FENCE`

## Description
Multi-lane adversarial examination envelope for A2_VS_A1_ROLE_SPLIT_FENCE

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: a2_vs_a1_role_split_fence is structurally necessary because: Explicit role fence: A2 owns refinery (broad reading, mass distillation, source-to-residue reduction, family triage, bat
- **adversarial_negative**: If a2_vs_a1_role_split_fence is removed, the following breaks: dependency chain on a2_a1_split, role_fence, refinery_ownership
- **success_condition**: SIM produces stable output when a2_vs_a1_role_split_fence is present
- **fail_condition**: SIM diverges or produces contradictory output without a2_vs_a1_role_split_fence
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[A2_VS_A1_ROLE_SPLIT_FENCE]]

## Inward Relations
- [[A2_VS_A1_ROLE_SPLIT_FENCE_COMPILED]] → **COMPILED_FROM**
