---
skill_id: a1-cartridge-graph-builder
name: a1-cartridge-graph-builder
description: Materialize the bounded A1 cartridge owner graph from the live A1 stripped owner graph and current cartridge doctrine, or fail closed if only witness-side stripped terms are present.
skill_type: refinement
source_type: repo_skill
applicable_layers: [A1_CARTRIDGE]
applicable_graphs: [strategy]
inputs: [a1_stripped_graph_v1, a1_cartridge_review, a1_cartridge_cross_judgment, a1_entropy_diversity_alias_lift_pack]
outputs: [a1_cartridge_graph_v1, a1_cartridge_graph_audit]
related_skills: [a1-stripped-graph-builder, a1-cartridge-assembler, nested-graph-layer-auditor, graph-capability-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded seventh nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/a1-cartridge-graph-builder/SKILL.md
  gemini: system_v4/skill_specs/a1-cartridge-graph-builder/SKILL.md
  shell: system_v4/skills/a1_cartridge_graph_builder.py
---

# A1 Cartridge Graph Builder

Use this skill when `A1_STRIPPED` is already materialized and the next bounded
task is to emit only those cartridge-layer nodes that current doctrine really
permits.

## Purpose

- build one explicit owner surface for exact stripped terms that are truly cartridge-packageable
- keep witness-only or deferred stripped terms out of the cartridge owner graph
- write only the explicit wrapper edge already authorized by the live assembler

## Execute Now

1. Load:
   - `system_v4/a1_state/a1_stripped_graph_v1.json`
   - `system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md`
   - `system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
2. Include only exact A1_STRIPPED terms that current cartridge doctrine treats as packageable fuel.
3. Emit only:
   - cartridge node(s)
   - `PACKAGED_FROM`
4. Fail closed if the pass would require promoting witness-side stripped terms into cartridge fuel.

## Quality Gates

- Do not treat family-level cartridge PASS as sufficient for exact-term packaging.
- Do not invent internal cartridge strategy/dependency edges.
- Do not promote downstream `COMPILED_FROM` edges into cartridge-owner doctrine.
