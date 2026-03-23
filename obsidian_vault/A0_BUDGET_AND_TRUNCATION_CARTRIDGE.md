---
id: "A1_CARTRIDGE::A0_BUDGET_AND_TRUNCATION"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# A0_BUDGET_AND_TRUNCATION_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::A0_BUDGET_AND_TRUNCATION`

## Description
Multi-lane adversarial examination envelope for A0_BUDGET_AND_TRUNCATION

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: a0_budget_and_truncation is structurally necessary because: Budget enforcement via max_items, max_sims, max_wall_ms. Deterministic truncation on overflow: drop lowest-priority buck
- **adversarial_negative**: If a0_budget_and_truncation is removed, the following breaks: dependency chain on compiler, budget, determinism
- **success_condition**: SIM produces stable output when a0_budget_and_truncation is present
- **fail_condition**: SIM diverges or produces contradictory output without a0_budget_and_truncation
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[A0_BUDGET_AND_TRUNCATION]]

## Inward Relations
- [[A0_BUDGET_AND_TRUNCATION_COMPILED]] → **COMPILED_FROM**
