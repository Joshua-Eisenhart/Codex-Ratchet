---
skill_id: a1-stripped-graph-builder
name: a1-stripped-graph-builder
description: Materialize the bounded A1 stripped owner graph from the live A1 jargoned owner graph and current A1 admissibility doctrine, or fail closed if only witness-side terms are present.
skill_type: refinement
source_type: repo_skill
applicable_layers: [A1_STRIPPED]
applicable_graphs: [dependency]
inputs: [a1_jargoned_graph_v1, a2_to_a1_family_slice, a1_rosetta_batch, a1_entropy_diversity_structure_lift_pack, a1_live_family_hint_coverage]
outputs: [a1_stripped_graph_v1, a1_stripped_graph_audit]
related_skills: [a1-jargoned-graph-builder, a1-jargoned-scope-aligner, a1-rosetta-stripper, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded sixth nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/a1-stripped-graph-builder/SKILL.md
  gemini: system_v4/skill_specs/a1-stripped-graph-builder/SKILL.md
  shell: system_v4/skills/a1_stripped_graph_builder.py
---

# A1 Stripped Graph Builder

Use this skill when `A1_JARGONED` is already materialized and the next bounded
task is to emit only those stripped-layer nodes that current A1 doctrine really
permits.

## Purpose

- strip only those current jargoned terms whose exact stripped landing is itself
  justified by live repo-held doctrine
- keep witness-only terms out of the stripped owner graph
- write only the explicit strip bridge edges

## Execute Now

1. Load:
   - `system_v4/a1_state/a1_jargoned_graph_v1.json`
   - `system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json`
   - `system_v3/a1_state/A1_ROSETTA_BATCH__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md`
   - `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
2. Include only current A1_JARGONED terms whose exact stripped landing term is
   currently justified as at least `PASSENGER_ONLY`.
3. Emit only:
   - stripped node(s)
   - `STRIPPED_FROM`
   - `ROSETTA_MAP`
4. Do not emit dependency edges yet.

## Quality Gates

- Do not use `A1_GRAPH_PROJECTION.json` as a source for this pass.
- Do not materialize witness-only terms into `A1_STRIPPED`.
- Do not treat family-level passenger survival as sufficient if the exact
  stripped landing remains witness-side or unnamed.
- Do not invent stripped-layer dependencies from prose or support refs.
