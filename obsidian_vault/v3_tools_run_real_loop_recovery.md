---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_run_real_loop_recovery::d3ce2da158fa6b3c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_run_real_loop_recovery
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_run_real_loop_recovery::d3ce2da158fa6b3c`

## Description
run_real_loop_recovery.py (20671B): from __future__ import annotations  import hashlib import json import re import shutil import zipfile from pathlib import Path   BEGIN_RECORD_RE = re.compile(r"^BEGIN EXPORT_RECORD (\d{8})$") END_RECORD_RE = re.compile(r"^END EXPORT_RECORD (\d{8})$")

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[v4_boot_recovery_05_overall_recovery_integration__20]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_real_loop_recovery_bridge_from_]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_real_loop_recovery_cycle]]

## Inward Relations
- [[run_codex_browser_launch_from_capture_record.py]] → **SOURCE_MAP_PASS**
- [[a2_state_v3_a2_update_note__run_real_loop_recovery_e]] → **EXCLUDES**
- [[a2_state_v3_a2_update_note__run_real_loop_recovery_m]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_dedicated_recovery_d]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_recovery_entrypoint_]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_recovery_module_spli]] → **EXCLUDES**
- [[a2_update_note__run_real_loop_soft_recovery_warnin]] → **EXCLUDES**
- [[test_run_real_loop_recovery_cycle_py]] → **EXCLUDES**
- [[run_real_loop_recovery_bridge_from_work_py]] → **EXCLUDES**
- [[run_real_loop_recovery_py]] → **EXCLUDES**
- [[run_real_loop_recovery_cycle_py]] → **EXCLUDES**
- [[v3_runtime_test_run_real_loop_recovery_cycle]] → **STRUCTURALLY_RELATED**
