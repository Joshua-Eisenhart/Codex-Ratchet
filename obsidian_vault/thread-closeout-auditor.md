---
id: "SKILL::thread-closeout-auditor"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# thread-closeout-auditor
**Node ID:** `SKILL::thread-closeout-auditor`

## Description
Audit thread closeout quality

## Properties
- **skill_type**: audit
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/thread-closeout-auditor/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/thread-closeout-auditor/SKILL.md", "gemini": "system_v4/skill_specs/thread-closeout-auditor/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]

## Inward Relations
- [[closeout-result-ingest]] → **RELATED_TO**
