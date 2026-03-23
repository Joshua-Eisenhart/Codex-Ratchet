---
id: "A1_CARTRIDGE::KILL_IF_SEMANTICS"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# KILL_IF_SEMANTICS_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::KILL_IF_SEMANTICS`

## Description
Multi-lane adversarial examination envelope for KILL_IF_SEMANTICS

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: kill_if_semantics is structurally necessary because: KILL_IF is declarative and idempotent. An item is KILLED iff: (1) item declares KILL_IF <ID> CORR <COND_TOKEN>, (2) SIM_
- **adversarial_negative**: If kill_if_semantics is removed, the following breaks: dependency chain on kernel, kill, evidence
- **success_condition**: SIM produces stable output when kill_if_semantics is present
- **fail_condition**: SIM diverges or produces contradictory output without kill_if_semantics
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[KILL_IF_SEMANTICS]]

## Inward Relations
- [[KILL_IF_SEMANTICS_COMPILED]] → **COMPILED_FROM**
