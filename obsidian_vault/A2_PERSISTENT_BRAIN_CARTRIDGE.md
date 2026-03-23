---
id: "A1_CARTRIDGE::A2_PERSISTENT_BRAIN"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# A2_PERSISTENT_BRAIN_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::A2_PERSISTENT_BRAIN`

## Description
Multi-lane adversarial examination envelope for A2_PERSISTENT_BRAIN

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: a2_persistent_brain is structurally necessary because: A2's authorized persistence lives strictly in canon files (e.g., memory.jsonl, doc_index.json). Overlays and derivations
- **adversarial_negative**: If a2_persistent_brain is removed, the following breaks: dependency chain on a2, memory, canon
- **success_condition**: SIM produces stable output when a2_persistent_brain is present
- **fail_condition**: SIM diverges or produces contradictory output without a2_persistent_brain
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[A2_PERSISTENT_BRAIN]]

## Inward Relations
- [[A2_PERSISTENT_BRAIN_COMPILED]] → **COMPILED_FROM**
