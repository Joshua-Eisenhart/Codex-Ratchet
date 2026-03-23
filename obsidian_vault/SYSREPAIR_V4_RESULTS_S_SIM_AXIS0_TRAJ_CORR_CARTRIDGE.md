---
id: "A1_CARTRIDGE::SYSREPAIR_V4_RESULTS_S_SIM_AXIS0_TRAJ_CORR"
type: "CARTRIDGE_PACKAGE"
layer: "A1_CARTRIDGE"
authority: "CROSS_VALIDATED"
---

# SYSREPAIR_V4_RESULTS_S_SIM_AXIS0_TRAJ_CORR_CARTRIDGE
**Node ID:** `A1_CARTRIDGE::SYSREPAIR_V4_RESULTS_S_SIM_AXIS0_TRAJ_CORR`

## Description
Multi-lane adversarial examination envelope for SYSREPAIR_V4_RESULTS_S_SIM_AXIS0_TRAJ_CORR

## Properties
- **candidate_shape**: SIM_SPEC
- **steelman_positive**: sysrepair_v4_results_s_sim_axis0_traj_corr_ is structurally necessary because: results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json (460B): {   "MI_mean": 0.35777832792995096,   "SAgB_mean": 0.216697779199112
- **adversarial_negative**: If sysrepair_v4_results_s_sim_axis0_traj_corr_ is removed, the following breaks: dependency chain on sysrepair_v4, json, final_sweep
- **success_condition**: SIM produces stable output when sysrepair_v4_results_s_sim_axis0_traj_corr_ is present
- **fail_condition**: SIM diverges or produces contradictory output without sysrepair_v4_results_s_sim_axis0_traj_corr_
- **legacy_tagged_utc**: 2026-03-19T08:09:33Z

## Outward Relations
- **PACKAGED_FROM** → [[SYSREPAIR_V4_RESULTS_S_SIM_AXIS0_TRAJ_CORR]]

## Inward Relations
- [[SYSREPAIR_V4_RESULTS_S_SIM_AXIS0_TRAJ_CORR_COMPILED]] → **COMPILED_FROM**
