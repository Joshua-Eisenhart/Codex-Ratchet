---
id: "SKILL::a1-stripped-exact-term-aligner"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-stripped-exact-term-aligner
**Node ID:** `SKILL::a1-stripped-exact-term-aligner`

## Description
Resolve exact stripped-term admissibility for a bounded A1 alias term, write an explicit correction audit, and re-materialize the stripped owner graph from the corrected doctrine.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-stripped-exact-term-aligner/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_STRIPPED"]
- **applicable_trust_zones**: ["A1_STRIPPED"]
- **applicable_graphs**: ["dependency"]
- **inputs**: ["a1_stripped_graph_v1", "a1_cartridge_graph_v1", "a1_live_family_hint_coverage", "a1_entropy_diversity_alias_lift_pack", "a1_cartridge_reviews"]
- **outputs**: ["a1_stripped_exact_term_alignment_audit", "a1_stripped_graph_v1"]
- **adapters**: {"codex": "system_v4/skill_specs/a1-stripped-exact-term-aligner/SKILL.md", "gemini": "system_v4/skill_specs/a1-stripped-exact-term-aligner/SKILL.md", "shell": "system_v4/skills/a1_stripped_exact_term_
- **related_skills**: ["a1-stripped-graph-builder", "a1-cartridge-graph-builder", "nested-graph-layer-auditor", "graph-capability-auditor"]

## Outward Relations
- **RELATED_TO** → [[a1-stripped-graph-builder]]
- **RELATED_TO** → [[a1-cartridge-graph-builder]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[graph-capability-auditor]]

## Inward Relations
- [[a1-stripped-term-plan-aligner]] → **RELATED_TO**
