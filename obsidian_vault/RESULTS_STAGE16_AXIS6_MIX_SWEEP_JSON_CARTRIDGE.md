---
id: "A1_CARTRIDGE::RESULTS_STAGE16_AXIS6_MIX_SWEEP_JSON"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# RESULTS_STAGE16_AXIS6_MIX_SWEEP_JSON_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::RESULTS_STAGE16_AXIS6_MIX_SWEEP_JSON`

## Description
Multi-lane adversarial examination envelope for RESULTS_STAGE16_AXIS6_MIX_SWEEP_JSON

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: results_stage16_axis6_mix_sweep_json is structurally necessary because: Unprocessed File Type (results_stage16_axis6_mix_sweep.json): { | "n_vec": [ | 0.3,
- **adversarial_negative**: If results_stage16_axis6_mix_sweep_json is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when results_stage16_axis6_mix_sweep_json is present
- **fail_condition**: SIM diverges or produces contradictory output without results_stage16_axis6_mix_sweep_json
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[RESULTS_STAGE16_AXIS6_MIX_SWEEP_JSON]]

## Inward Relations
- [[RESULTS_STAGE16_AXIS6_MIX_SWEEP_JSON_COMPILED]] → **COMPILED_FROM**
