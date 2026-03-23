---
skill_id: a1-stripped-term-plan-aligner
name: a1-stripped-term-plan-aligner
description: Resolve whether a bounded passenger family term has any honest stripped landing under current repo-held doctrine, write an explicit negative-or-positive audit, and keep A1 fail-closed when no exact landing exists.
skill_type: correction
source_type: repo_skill
applicable_layers: [A1_STRIPPED]
applicable_graphs: [dependency]
inputs: [a1_jargoned_graph_v1, a1_stripped_graph_v1, a1_cartridge_graph_v1, a1_family_doctrine_surfaces]
outputs: [a1_stripped_term_plan_alignment_audit, a1_stripped_graph_v1, a1_cartridge_graph_v1]
related_skills: [a1-stripped-graph-builder, a1-stripped-exact-term-aligner, a1-cartridge-graph-builder, nested-graph-layer-auditor, graph-capability-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A1 family-level stripped landing correction lane"
adapters:
  codex: system_v4/skill_specs/a1-stripped-term-plan-aligner/SKILL.md
  gemini: system_v4/skill_specs/a1-stripped-term-plan-aligner/SKILL.md
  shell: system_v4/skills/a1_stripped_term_plan_aligner.py
---

# A1 Stripped Term-Plan Aligner

Use this skill when a bounded A1 passenger family term may be surviving at the
family level but still lacks any honest exact stripped landing.

## Purpose

- separate family-level passenger survival from exact stripped landing
- preserve the block explicitly when doctrine does not name a valid exact term
- keep downstream A1_CARTRIDGE honest by re-materializing it from the corrected stripped result

## Execute Now

1. Load:
   - `system_v4/a1_state/a1_jargoned_graph_v1.json`
   - `system_v4/a1_state/a1_stripped_graph_v1.json`
   - `system_v4/a1_state/a1_cartridge_graph_v1.json`
   - `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
   - `system_v3/a1_state/A1_ROSETTA_BATCH__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md`
   - `system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
2. Decide whether `correlation_diversity_functional` has any current honest exact stripped landing.
3. If not, keep `A1_STRIPPED` fail-closed and rerun `A1_CARTRIDGE` from that blocked state.
4. Emit:
   - `A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md`
   - refreshed `a1_stripped_graph_v1.json`
   - refreshed `a1_cartridge_graph_v1.json`

## Quality Gates

- Do not treat family-level `PASSENGER_ONLY` as enough for exact stripped landing.
- Do not reopen `A1_JARGONED` when the issue is exact landing, not scope.
- Do not invent a replacement stripped node unless a current repo-held doctrine surface names it.
- If the result is negative, point the next correction lane back to `A2`, not deeper into blocked `A1`.
