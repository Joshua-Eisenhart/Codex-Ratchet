---
id: "SKILL::intent-control-surface-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# intent-control-surface-builder
**Node ID:** `SKILL::intent-control-surface-builder`

## Description
Build the current derived A2 intent-control surface from witness and refinery intent/context signals.

## Properties
- **skill_type**: bridge
- **source_type**: python_module
- **source_path**: system_v4/skills/intent_control_surface_builder.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL"]
- **applicable_graphs**: ["control"]
- **inputs**: ["witness_corpus_v1", "system_graph_a2_refinery"]
- **outputs**: ["A2_INTENT_CONTROL_SURFACE_v1"]
- **adapters**: {"shell": "system_v4/skills/intent_control_surface_builder.py"}
- **related_skills**: ["witness-recorder", "runtime-graph-bridge", "bounded-improve-operator"]

## Outward Relations
- **RELATED_TO** → [[witness-recorder]]
- **RELATED_TO** → [[runtime-graph-bridge]]
- **RELATED_TO** → [[bounded-improve-operator]]
- **SKILL_OPERATES_ON** → [[a2_controller_dispatch_first]]

## Inward Relations
- [[runtime-context-snapshot]] → **RELATED_TO**
- [[intent-refinement-graph-builder]] → **RELATED_TO**
