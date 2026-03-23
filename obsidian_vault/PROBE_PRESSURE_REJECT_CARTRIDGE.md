---
id: "A1_CARTRIDGE::PROBE_PRESSURE_REJECT"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# PROBE_PRESSURE_REJECT_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::PROBE_PRESSURE_REJECT`

## Description
Multi-lane adversarial examination envelope for PROBE_PRESSURE_REJECT

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: probe_pressure_reject is structurally necessary because: Archived Work File: BEGIN EXPORT_BLOCK v1
- **adversarial_negative**: If probe_pressure_reject is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when probe_pressure_reject is present
- **fail_condition**: SIM diverges or produces contradictory output without probe_pressure_reject
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[PROBE_PRESSURE_REJECT]]

## Inward Relations
- [[PROBE_PRESSURE_REJECT_COMPILED]] → **COMPILED_FROM**
