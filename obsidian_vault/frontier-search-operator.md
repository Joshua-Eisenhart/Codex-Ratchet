---
id: "SKILL::frontier-search-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# frontier-search-operator
**Node ID:** `SKILL::frontier-search-operator`

## Description
Frontier Search Operator

## Properties
- **skill_type**: refinement
- **source_type**: python_module
- **source_path**: system_v4/skills/frontier_search_operator.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL"]
- **applicable_graphs**: ["a2_low_control_graph_v1"]
- **inputs**: ["runtime_state", "transforms"]
- **outputs**: ["search_result", "motifs"]
- **adapters**: {"shell": "system_v4/skills/frontier_search_operator.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
