---
id: "A1_CARTRIDGE::SIM_EVIDENCE_V1"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# SIM_EVIDENCE_V1_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::SIM_EVIDENCE_V1`

## Description
Multi-lane adversarial examination envelope for SIM_EVIDENCE_V1

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: sim_evidence_v1 is structurally necessary because: Archived Work File: This specification defines the canonical deterministic evidence container emitted by SIM and transpo
- **adversarial_negative**: If sim_evidence_v1 is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when sim_evidence_v1 is present
- **fail_condition**: SIM diverges or produces contradictory output without sim_evidence_v1
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[SIM_EVIDENCE_V1]]

## Inward Relations
- [[SIM_EVIDENCE_V1_COMPILED]] → **COMPILED_FROM**
