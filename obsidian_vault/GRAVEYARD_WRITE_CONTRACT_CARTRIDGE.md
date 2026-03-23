---
id: "A1_CARTRIDGE::GRAVEYARD_WRITE_CONTRACT"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# GRAVEYARD_WRITE_CONTRACT_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::GRAVEYARD_WRITE_CONTRACT`

## Description
Multi-lane adversarial examination envelope for GRAVEYARD_WRITE_CONTRACT

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: graveyard_write_contract is structurally necessary because: Every rejection must include candidate_id, reason_tag, raw_lines, failure_class (B_KILL or SIM_KILL), target_ref. Meanin
- **adversarial_negative**: If graveyard_write_contract is removed, the following breaks: dependency chain on graveyard, evidence, lineage
- **success_condition**: SIM produces stable output when graveyard_write_contract is present
- **fail_condition**: SIM diverges or produces contradictory output without graveyard_write_contract
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[GRAVEYARD_WRITE_CONTRACT]]

## Inward Relations
- [[GRAVEYARD_WRITE_CONTRACT_COMPILED]] → **COMPILED_FROM**
