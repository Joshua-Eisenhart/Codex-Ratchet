---
skill_id: a2-entropy-bridge-helper-decomposition-control
name: a2-entropy-bridge-helper-decomposition-control
description: Run one bounded A2-only helper-decomposition control pass for correlation_diversity_functional and write an explicit audit that confirms compound bridge heads stay proposal-side while colder witnesses remain the executable floor.
skill_type: correction
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT]
applicable_graphs: [concept]
inputs: [a2_stage1_operatorized_entropy_head_refinement_audit, helper_decomposition_control_surface, executable_entrypoint_surface]
outputs: [a2_entropy_bridge_helper_decomposition_control_audit]
related_skills: [a2-stage1-operatorized-entropy-head-refinement, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A2 correction lane for entropy bridge helper-decomposition control"
adapters:
  codex: system_v4/skill_specs/a2-entropy-bridge-helper-decomposition-control/SKILL.md
  gemini: system_v4/skill_specs/a2-entropy-bridge-helper-decomposition-control/SKILL.md
  shell: system_v4/skills/a2_entropy_bridge_helper_decomposition_control.py
---

# A2 Entropy Bridge Helper Decomposition Control

Use this skill when the truthful next move is one bounded A2-only pass that
freezes the helper-decomposition barrier for
`correlation_diversity_functional`, after the Stage-1 entropy-head refinement
already preserved the blocker explicitly.

## Purpose

- confirm the real blocker is helper decomposition under current lower-loop semantics
- keep compound bridge heads in proposal/control space instead of faking stripped admission
- preserve colder witness execution as the current executable default

## Execute Now

1. Load:
   - `system_v4/a2_state/audit_logs/A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_REFINEMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md`
   - `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
   - `system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md`
2. Decide whether the repo-held doctrine confirms:
   - compound bridge heads remain proposal/control-only
   - executable work stays on colder witnesses
   - alias/component-ladder work remains deferred
3. Emit:
   - `system_v4/a2_state/audit_logs/A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md`

## Quality Gates

- Stay A2-only; do not perform A1 stripped translation or cartridge packaging.
- Do not claim `correlation_diversity_functional` has earned direct executable admission.
- Do not reopen alias-first or component-ladder work as the default route unless the cited doctrine explicitly changes.
- If the doctrine does not line up, fail closed with explicit missing evidence.
