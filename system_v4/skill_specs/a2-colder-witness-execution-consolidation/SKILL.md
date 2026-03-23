---
skill_id: a2-colder-witness-execution-consolidation
name: a2-colder-witness-execution-consolidation
description: Run one bounded A2-only consolidation pass for the colder-witness executable branch around correlation_polarity and write an explicit audit that preserves the broad executable head/floor split without promoting direct structure heads.
skill_type: correction
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT]
applicable_graphs: [concept]
inputs: [a2_entropy_bridge_helper_decomposition_control_audit, entropy_executable_entrypoint_surface, entropy_correlation_executable_pack]
outputs: [colder_witness_execution_consolidation_audit]
related_skills: [a2-entropy-bridge-helper-decomposition-control, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A2 correction lane for colder-witness executable consolidation"
adapters:
  codex: system_v4/skill_specs/a2-colder-witness-execution-consolidation/SKILL.md
  gemini: system_v4/skill_specs/a2-colder-witness-execution-consolidation/SKILL.md
  shell: system_v4/skills/a2_colder_witness_execution_consolidation.py
---

# A2 Colder Witness Execution Consolidation

Use this skill when the truthful next move is one bounded A2-only pass that
consolidates the live executable entropy branch around `correlation_polarity`
after helper-decomposition control is already fixed.

## Purpose

- confirm the live executable head/floor split on the broad correlation-side route
- preserve the distinction between broad executable survival and narrow standalone failure
- hand off the next control move to branch-budget / merge tightening instead of fake landing work

## Execute Now

1. Load:
   - `system_v4/a2_state/audit_logs/A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
   - `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
   - `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
   - `system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_BRANCH_BUDGET_AND_MERGE_PACK__v1.md`
2. Decide whether the broad executable branch is still honestly centered on `correlation_polarity` with `correlation` as companion floor.
3. Emit:
   - `system_v4/a2_state/audit_logs/COLDER_WITNESS_EXECUTION_CONSOLIDATION__CORRELATION_POLARITY__2026_03_20__v1.md`

## Quality Gates

- Stay A2-only; do not perform A1 stripped translation or cartridge packaging.
- Do not treat `correlation_polarity` as a narrow standalone executable survivor if the doctrine still says the narrow route is too thin.
- Do not promote `correlation_diversity_functional` or other richer structure heads from this pass.
- If the broad branch remains valid, hand off the next control move to branch-budget / merge tightening.
