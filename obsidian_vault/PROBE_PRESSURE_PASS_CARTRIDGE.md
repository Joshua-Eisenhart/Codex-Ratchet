---
id: "A1_CARTRIDGE::PROBE_PRESSURE_PASS"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# PROBE_PRESSURE_PASS_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::PROBE_PRESSURE_PASS`

## Description
Multi-lane adversarial examination envelope for PROBE_PRESSURE_PASS

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: probe_pressure_pass is structurally necessary because: Archived Work File: BEGIN EXPORT_BLOCK v1
- **adversarial_negative**: If probe_pressure_pass is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when probe_pressure_pass is present
- **fail_condition**: SIM diverges or produces contradictory output without probe_pressure_pass
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[PROBE_PRESSURE_PASS]]

## Inward Relations
- [[PROBE_PRESSURE_PASS_COMPILED]] → **COMPILED_FROM**
