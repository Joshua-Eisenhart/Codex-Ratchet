---
id: "SKILL::thread-dispatch-controller"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# thread-dispatch-controller
**Node ID:** `SKILL::thread-dispatch-controller`

## Description
Manage thread dispatch and routing

## Properties
- **skill_type**: orchestration
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/thread-dispatch-controller/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/thread-dispatch-controller/SKILL.md", "gemini": "system_v4/skill_specs/thread-dispatch-controller/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[run-real-ratchet]]
- **SKILL_OPERATES_ON** → [[a2_controller_dispatch_first]]
- **SKILL_OPERATES_ON** → [[eight_phase_gate_pipeline]]
