---
id: "SKILL::runtime-graph-bridge"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# runtime-graph-bridge
**Node ID:** `SKILL::runtime-graph-bridge`

## Description
Map B/SIM outcomes back into master graph

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/runtime_graph_bridge.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED", "SIM_EVIDENCED", "GRAVEYARD"]
- **applicable_trust_zones**: ["B_ADJUDICATED", "SIM_EVIDENCED", "GRAVEYARD"]
- **applicable_graphs**: ["runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/runtime_graph_bridge.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]
- **SKILL_OPERATES_ON** → [[GRAPH_AS_CONTROL_SUBSTRATE]]

## Inward Relations
- [[browser-automation]] → **RELATED_TO**
- [[intent-control-surface-builder]] → **RELATED_TO**
