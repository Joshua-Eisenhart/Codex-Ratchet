---
id: "SKILL::a1-jargoned-scope-aligner"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-jargoned-scope-aligner
**Node ID:** `SKILL::a1-jargoned-scope-aligner`

## Description
Align the queued A1_JARGONED family scope with live packet-backed Rosetta fuel, minting only defensible anchored terms and preserving blocked scope residue explicitly.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-jargoned-scope-aligner/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_JARGONED"]
- **applicable_trust_zones**: ["A1_JARGONED"]
- **applicable_graphs**: ["rosetta"]
- **inputs**: ["rosetta_v2", "a1_queue_candidate_registry", "a2_to_a1_family_slice", "system_graph_a2_refinery"]
- **outputs**: ["rosetta_v2", "a1_jargoned_handoff", "a1_jargoned_scope_alignment_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a1-jargoned-scope-aligner/SKILL.md", "gemini": "system_v4/skill_specs/a1-jargoned-scope-aligner/SKILL.md", "shell": "system_v4/skills/a1_jargoned_scope_aligner.py"}
- **related_skills**: ["a1-jargoned-graph-builder", "a1-rosetta-stripper", "identity-registry-builder", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[a1-jargoned-graph-builder]]
- **RELATED_TO** → [[a1-rosetta-stripper]]
- **RELATED_TO** → [[identity-registry-builder]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]

## Inward Relations
- [[a1-stripped-graph-builder]] → **RELATED_TO**
