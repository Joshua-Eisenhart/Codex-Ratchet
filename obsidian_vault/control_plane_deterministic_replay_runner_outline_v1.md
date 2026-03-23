---
id: "A2_3::SOURCE_MAP_PASS::control_plane_deterministic_replay_runner_outline_v1::28dab732eff6c732"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_deterministic_replay_runner_outline_v1
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_deterministic_replay_runner_outline_v1::28dab732eff6c732`

## Description
DETERMINISTIC_REPLAY_RUNNER_OUTLINE_v1.md (1609B): # DETERMINISTIC_REPLAY_RUNNER_OUTLINE v1  ## Script target `runtime/bootpack_b_kernel_v1/tools/replay_runner.py`  ## Inputs - ordered ZIP path list (explicit ordering; no filesystem enumeration reliance) - initial canonical state snapshot bytes - compiler_version - last_sequence table initialization

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[deterministic_replay_runner]]
- **DEPENDS_ON** → [[deterministic_replay_runner_outline_v1]]
- **DEPENDS_ON** → [[input]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[deterministic_dual_replay]]
- **STRUCTURALLY_RELATED** → [[sim_deterministic_replay]]
- **EXCLUDES** → [[v3_runtime_replay_runner]]
- **EXCLUDES** → [[replay_runner_py]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[deterministic_dual_replay]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_REPLAY_HASH_EQUALITY]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_DUAL_REPLAY]] → **STRUCTURALLY_RELATED**
