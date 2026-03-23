---
id: "A1_CARTRIDGE::FIX_PROBE_001_PRESSURE_PARK"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# FIX_PROBE_001_PRESSURE_PARK_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::FIX_PROBE_001_PRESSURE_PARK`

## Description
Multi-lane adversarial examination envelope for FIX_PROBE_001_PRESSURE_PARK

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: fix_probe_001_pressure_park is structurally necessary because: Archived Work File: BEGIN EXPORT_BLOCK vN
- **adversarial_negative**: If fix_probe_001_pressure_park is removed, the following breaks: dependency chain on work_archive, audit_tmp
- **success_condition**: SIM produces stable output when fix_probe_001_pressure_park is present
- **fail_condition**: SIM diverges or produces contradictory output without fix_probe_001_pressure_park
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[FIX_PROBE_001_PRESSURE_PARK]]

## Inward Relations
- [[FIX_PROBE_001_PRESSURE_PARK_COMPILED]] → **COMPILED_FROM**
