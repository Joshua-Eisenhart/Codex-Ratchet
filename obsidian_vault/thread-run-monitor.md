---
id: "SKILL::thread-run-monitor"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# thread-run-monitor
**Node ID:** `SKILL::thread-run-monitor`

## Description
Monitor running threads

## Properties
- **skill_type**: orchestration
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/thread-run-monitor/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/thread-run-monitor/SKILL.md", "gemini": "system_v4/skill_specs/thread-run-monitor/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[run-real-ratchet]]

## Inward Relations
- [[nested-graph-layer-auditor]] → **RELATED_TO**
