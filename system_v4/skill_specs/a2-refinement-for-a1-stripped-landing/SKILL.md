---
skill_id: a2-refinement-for-a1-stripped-landing
name: a2-refinement-for-a1-stripped-landing
description: Run one bounded A2-only correction pass for a stalled direct-structure target whose A1 stripped landing failed closed, and write an explicit audit that either names a current source-anchored landing or preserves the blocker.
skill_type: correction
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT]
applicable_graphs: [concept]
inputs: [a1_stripped_graph_v1, a1_stripped_term_plan_alignment_audit, a2_stage1_entropy_head_doctrine]
outputs: [a2_refinement_for_a1_stripped_landing_audit]
related_skills: [a2-mid-refinement-graph-builder, a1-stripped-term-plan-aligner, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A2 correction lane for stalled stripped landing"
adapters:
  codex: system_v4/skill_specs/a2-refinement-for-a1-stripped-landing/SKILL.md
  gemini: system_v4/skill_specs/a2-refinement-for-a1-stripped-landing/SKILL.md
  shell: system_v4/skills/a2_refinement_for_a1_stripped_landing.py
---

# A2 Refinement For A1 Stripped Landing

Use this skill when `A1_STRIPPED` has already failed closed for a bounded family
and the next truthful move is to push the unresolved landing question back up
into A2 refinement.

## Purpose

- keep landing failures upstream instead of papering them over in A1
- decide whether any current source-anchored exact landing exists
- preserve the blocker explicitly when no current landing exists

## Execute Now

1. Load:
   - `system_v4/a1_state/a1_stripped_graph_v1.json`
   - `system_v4/a2_state/audit_logs/A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md`
   - `system_v3/a2_state/A2_UPDATE_NOTE__STAGE1_OPERATORIZED_ENTROPY_HEAD_GROUNDING__2026_03_17__v1.md`
   - `system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__STAGE1_OPERATORIZED_ENTROPY_HEAD_GROUNDING__2026_03_17__v1.md`
   - `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
   - `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
   - `system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md`
2. Decide whether `correlation_diversity_functional` has any current source-anchored exact landing that could later support `A1_STRIPPED`.
3. Emit:
   - `A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md`

## Quality Gates

- Stay A2-only; do not perform A1 translation or packaging in this pass.
- Do not treat family-level interest or passenger survival as enough for exact landing.
- Do not upgrade witness-floor aliases into stripped candidates.
- If the answer is still negative, point the next queue unit at the next bounded A2 lane, not back into blocked A1.
