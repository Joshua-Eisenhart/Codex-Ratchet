---
id: "SKILL::a1-stripped-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-stripped-graph-builder
**Node ID:** `SKILL::a1-stripped-graph-builder`

## Description
Materialize the bounded A1 stripped owner graph from the live A1 jargoned owner graph and current A1 admissibility doctrine, or fail closed if only witness-side terms are present.

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-stripped-graph-builder/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_STRIPPED", "PHASE_A1_STRIPPER"]
- **applicable_trust_zones**: ["A1_STRIPPED", "PHASE_A1_STRIPPER"]
- **applicable_graphs**: ["dependency"]
- **inputs**: ["a1_jargoned_graph_v1", "a2_to_a1_family_slice", "a1_rosetta_batch", "a1_entropy_diversity_structure_lift_pack", "a1_live_family_hint_coverage"]
- **outputs**: ["a1_stripped_graph_v1", "a1_stripped_graph_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a1-stripped-graph-builder/SKILL.md", "gemini": "system_v4/skill_specs/a1-stripped-graph-builder/SKILL.md", "shell": "system_v4/skills/a1_stripped_graph_builder.py"}
- **related_skills**: ["a1-jargoned-graph-builder", "a1-jargoned-scope-aligner", "a1-rosetta-stripper", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[a1-jargoned-graph-builder]]
- **RELATED_TO** → [[a1-jargoned-scope-aligner]]
- **RELATED_TO** → [[a1-rosetta-stripper]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]

## Inward Relations
- [[a1-cartridge-graph-builder]] → **RELATED_TO**
- [[a1-stripped-exact-term-aligner]] → **RELATED_TO**
- [[a1-stripped-term-plan-aligner]] → **RELATED_TO**
