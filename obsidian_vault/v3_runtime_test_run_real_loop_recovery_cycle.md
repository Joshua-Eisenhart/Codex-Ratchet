---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_run_real_loop_recovery_cycle::98c335bbc0525e60"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_run_real_loop_recovery_cycle
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_run_real_loop_recovery_cycle::98c335bbc0525e60`

## Description
test_run_real_loop_recovery_cycle.py (2037B): from __future__ import annotations  import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[3] sys.path.insert(0, str(BASE / "tools"))  from run_real_loop_recovery_cycle import (  # noqa: E402     _inject_recovery

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_tools_run_real_loop_recovery_cycle]]
- **EXCLUDES** → [[v4_boot_recovery_05_overall_recovery_integration__20]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_real_loop_recovery]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_real_loop_recovery_bridge_from_]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[test_run_real_loop_recovery_cycle_py]] → **STRUCTURALLY_RELATED**
- [[run_real_loop_recovery_cycle_py]] → **STRUCTURALLY_RELATED**
- [[a2_state_v3_a2_update_note__run_real_loop_recovery_e]] → **EXCLUDES**
- [[a2_state_v3_a2_update_note__run_real_loop_recovery_m]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_dedicated_recovery_d]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_recovery_entrypoint_]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_recovery_module_spli]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_soft_recovery_warnin]] → **EXCLUDES**
- [[run_real_loop_recovery_bridge_from_work_py]] → **EXCLUDES**
- [[run_real_loop_recovery_py]] → **EXCLUDES**
