---
id: "SKILL::external-research-return-ingest"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# external-research-return-ingest
**Node ID:** `SKILL::external-research-return-ingest`

## Description
Ingest external research results

## Properties
- **skill_type**: bridge
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/external-research-return-ingest/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE"]
- **applicable_graphs**: ["provenance"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/external-research-return-ingest/SKILL.md", "gemini": "system_v4/skill_specs/external-research-return-ingest/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
