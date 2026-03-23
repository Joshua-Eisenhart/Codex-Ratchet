---
id: "A1_CARTRIDGE::SIM_EVIDENCE"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# SIM_EVIDENCE_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::SIM_EVIDENCE`

## Description
Multi-lane adversarial examination envelope for SIM_EVIDENCE

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: sim_evidence is structurally necessary because: Canonical deterministic evidence container emitted by SIM. Bounded by BEGIN/END lines. Contains SIM_ID, CODE_HASH_SHA256
- **adversarial_negative**: If sim_evidence is removed, the following breaks: dependency chain on sim_evidence, container, primitive
- **success_condition**: SIM produces stable output when sim_evidence is present
- **fail_condition**: SIM diverges or produces contradictory output without sim_evidence
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[SIM_EVIDENCE]]

## Inward Relations
- [[SIM_EVIDENCE_COMPILED]] → **COMPILED_FROM**
