---
id: "SKILL::ratchet-reflect"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-reflect
**Node ID:** `SKILL::ratchet-reflect`

## Description
Find connections between concepts and weave the graph

## Properties
- **skill_type**: enrichment
- **source_type**: repo_skill
- **source_path**: system_v4/skills/ratchet-reflect/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["concept", "contradiction"]
- **inputs**: ["concept_id or recent concepts"]
- **outputs**: ["RELATED_TO edges", "OVERLAPS edges", "CONTRADICTS edges"]
- **adapters**: {"codex": "system_v4/skills/ratchet-reflect/SKILL.md", "gemini": "system_v4/skills/ratchet-reflect/SKILL.md"}
- **related_skills**: ["ratchet-reduce", "ratchet-reweave", "ratchet-verify"]

## Outward Relations
- **SKILL_FOLLOWS** → [[ratchet-reduce]]
- **SKILL_FOLLOWS** → [[ratchet-reweave]]
- **SKILL_FOLLOWS** → [[ratchet-verify]]
- **RELATED_TO** → [[ratchet-reduce]]
- **RELATED_TO** → [[ratchet-reweave]]
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[unitary_thread_b_ratchet]]

## Inward Relations
- [[ratchet-reduce]] → **SKILL_FOLLOWS**
- [[ratchet-reweave]] → **SKILL_FOLLOWS**
- [[ratchet-verify]] → **SKILL_FOLLOWS**
- [[ratchet-reduce]] → **RELATED_TO**
- [[ratchet-reweave]] → **RELATED_TO**
- [[ratchet-verify]] → **RELATED_TO**
