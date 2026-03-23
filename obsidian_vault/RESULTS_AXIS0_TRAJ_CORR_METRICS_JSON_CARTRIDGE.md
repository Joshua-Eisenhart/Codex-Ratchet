---
id: "A1_CARTRIDGE::RESULTS_AXIS0_TRAJ_CORR_METRICS_JSON"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# RESULTS_AXIS0_TRAJ_CORR_METRICS_JSON_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::RESULTS_AXIS0_TRAJ_CORR_METRICS_JSON`

## Description
Multi-lane adversarial examination envelope for RESULTS_AXIS0_TRAJ_CORR_METRICS_JSON

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: results_axis0_traj_corr_metrics_json is structurally necessary because: Unprocessed File Type (results_axis0_traj_corr_metrics.json): { | "BELL_SEQ01": { | "MI_final_mean": 0.00760471791203304
- **adversarial_negative**: If results_axis0_traj_corr_metrics_json is removed, the following breaks: dependency chain on system_file_scan
- **success_condition**: SIM produces stable output when results_axis0_traj_corr_metrics_json is present
- **fail_condition**: SIM diverges or produces contradictory output without results_axis0_traj_corr_metrics_json
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[RESULTS_AXIS0_TRAJ_CORR_METRICS_JSON]]

## Inward Relations
- [[RESULTS_AXIS0_TRAJ_CORR_METRICS_JSON_COMPILED]] → **COMPILED_FROM**
