---
id: "A2_3::ENGINE_PATTERN_PASS::B_Probe_Pressure_Rule::4ddef0a278b1c92e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# B_Probe_Pressure_Rule
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::B_Probe_Pressure_Rule::4ddef0a278b1c92e`

## Description
Per 10 newly accepted SPEC_HYP, require >= 1 newly accepted PROBE_HYP. Unmet pressure parks lowest-priority spec items.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[b_kernel_probe_pressure]]
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
- [[03_B_KERNEL_SPEC.md]] → **ENGINE_PATTERN_PASS**
