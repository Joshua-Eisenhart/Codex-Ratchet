---
id: "SKILL::ratchet-reduce"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-reduce
**Node ID:** `SKILL::ratchet-reduce`

## Description
Extract structured claims from source documents into graph concepts

## Properties
- **skill_type**: extraction
- **source_type**: repo_skill
- **source_path**: system_v4/skills/ratchet-reduce/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["provenance", "concept"]
- **inputs**: ["source_document_path"]
- **outputs**: ["EXTRACTED_CONCEPT nodes", "SOURCE_MAP edges"]
- **adapters**: {"codex": "system_v4/skills/ratchet-reduce/SKILL.md", "gemini": "system_v4/skills/ratchet-reduce/SKILL.md"}
- **related_skills**: ["ratchet-reflect", "ratchet-reweave", "ratchet-verify"]

## Outward Relations
- **SKILL_FOLLOWS** → [[ratchet-reflect]]
- **SKILL_FOLLOWS** → [[ratchet-reweave]]
- **SKILL_FOLLOWS** → [[ratchet-verify]]
- **RELATED_TO** → [[ratchet-reflect]]
- **RELATED_TO** → [[ratchet-reweave]]
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[unitary_thread_b_ratchet]]

## Inward Relations
- [[ratchet-reflect]] → **SKILL_FOLLOWS**
- [[ratchet-reweave]] → **SKILL_FOLLOWS**
- [[ratchet-verify]] → **SKILL_FOLLOWS**
- [[ratchet-reflect]] → **RELATED_TO**
- [[ratchet-reweave]] → **RELATED_TO**
- [[ratchet-verify]] → **RELATED_TO**
- [[wiggle-lane-runner]] → **RELATED_TO**
