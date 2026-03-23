---
id: "SKILL::runtime-context-snapshot"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# runtime-context-snapshot
**Node ID:** `SKILL::runtime-context-snapshot`

## Description
Capture the current controller and A1 queue state into the append-only context witness spine.

## Properties
- **skill_type**: bridge
- **source_type**: python_module
- **source_path**: system_v4/skills/runtime_context_snapshot.py
- **status**: active
- **applicable_layers**: ["A2_3_INTAKE"]
- **applicable_trust_zones**: ["A2_3_INTAKE"]
- **applicable_graphs**: ["witness"]
- **inputs**: ["A2_CONTROLLER_LAUNCH_SPINE", "A1_QUEUE_STATUS_PACKET"]
- **outputs**: ["context_witness"]
- **adapters**: {"shell": "system_v4/skills/runtime_context_snapshot.py"}
- **related_skills**: ["witness-recorder", "intent-control-surface-builder"]

## Outward Relations
- **RELATED_TO** → [[witness-recorder]]
- **RELATED_TO** → [[intent-control-surface-builder]]
- **SKILL_OPERATES_ON** → [[kernel_seed_state]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[intent-refinement-graph-builder]] → **RELATED_TO**
- [[a2-brain-surface-refresher]] → **RELATED_TO**
