---
id: "A2_3::SOURCE_MAP_PASS::b_kernel_probe_pressure::6819e2e8be4c00d6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# b_kernel_probe_pressure
**Node ID:** `A2_3::SOURCE_MAP_PASS::b_kernel_probe_pressure::6819e2e8be4c00d6`

## Description
Requires at least 1 ACCEPTED PROBE_HYP per 10 ACCEPTED SPEC_HYP. Unmet pressure parks lower-priority specs.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[conformance_fix_probe_001_pressure_park]]
- **EXCLUDES** → [[sysrepair_v2_fix_probe_001_pressure_park]]
- **EXCLUDES** → [[sysrepair_v2_probe_pressure_park]]
- **EXCLUDES** → [[sysrepair_v2_probe_pressure_pass]]
- **EXCLUDES** → [[sysrepair_v2_probe_pressure_reject]]
- **EXCLUDES** → [[sysrepair_v3_fix_probe_001_pressure_park]]
- **EXCLUDES** → [[sysrepair_v3_probe_pressure_park]]
- **EXCLUDES** → [[sysrepair_v3_probe_pressure_pass]]
- **EXCLUDES** → [[sysrepair_v3_probe_pressure_reject]]
- **EXCLUDES** → [[sysrepair_v4_fix_probe_001_pressure_park]]
- **EXCLUDES** → [[sysrepair_v4_probe_pressure_park]]
- **EXCLUDES** → [[sysrepair_v4_probe_pressure_pass]]
- **EXCLUDES** → [[sysrepair_v4_probe_pressure_reject]]
- **EXCLUDES** → [[v3_runtime_probe_pressure_park]]
- **EXCLUDES** → [[v3_runtime_probe_pressure_pass]]
- **EXCLUDES** → [[v3_runtime_probe_pressure_reject]]
- **EXCLUDES** → [[probe_pressure_pass]]
- **EXCLUDES** → [[probe_pressure_reject]]
- **EXCLUDES** → [[probe_pressure_park]]
- **EXCLUDES** → [[fix_probe_001_pressure_park]]

## Inward Relations
- [[03_B_KERNEL_SPEC.md]] → **SOURCE_MAP_PASS**
- [[B_Probe_Pressure_Rule]] → **RELATED_TO**
