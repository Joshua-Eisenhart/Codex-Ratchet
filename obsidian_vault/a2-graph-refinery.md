---
id: "SKILL::a2-graph-refinery"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-graph-refinery
**Node ID:** `SKILL::a2-graph-refinery`

## Description
A2 graph refinery — intake, promotion, NX queries

## Properties
- **skill_type**: orchestration
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_graph_refinery.py
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["provenance", "concept", "contradiction"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/v4_graph_builder.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]
- **SKILL_OPERATES_ON** → [[GRAPH_AS_CONTROL_SUBSTRATE]]
- **SKILL_OPERATES_ON** → [[a2_canonical_schemas]]
