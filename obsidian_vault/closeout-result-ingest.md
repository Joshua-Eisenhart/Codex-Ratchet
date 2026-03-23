---
id: "SKILL::closeout-result-ingest"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# closeout-result-ingest
**Node ID:** `SKILL::closeout-result-ingest`

## Description
Ingest results from completed threads

## Properties
- **skill_type**: bridge
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/closeout-result-ingest/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/closeout-result-ingest/SKILL.md", "gemini": "system_v4/skill_specs/closeout-result-ingest/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[thread-closeout-auditor]]
