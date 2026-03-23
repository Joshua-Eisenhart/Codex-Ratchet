---
id: "SKILL::ratchet-reweave"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-reweave
**Node ID:** `SKILL::ratchet-reweave`

## Description
Update existing graph concepts with new knowledge (backward pass)

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skills/ratchet-reweave/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["concept", "contradiction"]
- **inputs**: ["concept_id or sparse/stale concepts"]
- **outputs**: ["Updated concept nodes", "New edges"]
- **adapters**: {"codex": "system_v4/skills/ratchet-reweave/SKILL.md", "gemini": "system_v4/skills/ratchet-reweave/SKILL.md"}
- **related_skills**: ["ratchet-reduce", "ratchet-reflect", "ratchet-verify"]

## Outward Relations
- **SKILL_FOLLOWS** → [[ratchet-reduce]]
- **SKILL_FOLLOWS** → [[ratchet-reflect]]
- **SKILL_FOLLOWS** → [[ratchet-verify]]
- **RELATED_TO** → [[ratchet-reduce]]
- **RELATED_TO** → [[ratchet-reflect]]
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[unitary_thread_b_ratchet]]

## Inward Relations
- [[ratchet-reduce]] → **SKILL_FOLLOWS**
- [[ratchet-reflect]] → **SKILL_FOLLOWS**
- [[ratchet-verify]] → **SKILL_FOLLOWS**
- [[brain-delta-consolidation]] → **RELATED_TO**
- [[ratchet-reduce]] → **RELATED_TO**
- [[ratchet-reflect]] → **RELATED_TO**
- [[ratchet-verify]] → **RELATED_TO**
