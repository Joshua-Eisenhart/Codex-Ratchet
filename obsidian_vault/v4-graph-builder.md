---
id: "SKILL::v4-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# v4-graph-builder
**Node ID:** `SKILL::v4-graph-builder`

## Description
Pydantic + NX + GraphML graph engine

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/v4_graph_builder.py
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: ["provenance", "concept", "contradiction", "dependency", "rosetta", "runtime", "graveyard"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/v4_graph_builder.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]
