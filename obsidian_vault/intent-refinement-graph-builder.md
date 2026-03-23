---
id: "SKILL::intent-refinement-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# intent-refinement-graph-builder
**Node ID:** `SKILL::intent-refinement-graph-builder`

## Description
Materialize graph-native intent/context signals and intent refinements from the witness corpus.

## Properties
- **skill_type**: bridge
- **source_type**: python_module
- **source_path**: system_v4/skills/intent_refinement_graph_builder.py
- **status**: active
- **applicable_layers**: ["A2_2_CANDIDATE"]
- **applicable_trust_zones**: ["A2_2_CANDIDATE"]
- **applicable_graphs**: ["system_graph_a2_refinery"]
- **inputs**: ["witness_corpus_v1", "system_graph_a2_refinery"]
- **outputs**: ["intent_refinement_graph_update"]
- **adapters**: {"shell": "system_v4/skills/intent_refinement_graph_builder.py"}
- **related_skills**: ["runtime-context-snapshot", "intent-control-surface-builder"]

## Outward Relations
- **RELATED_TO** → [[runtime-context-snapshot]]
- **RELATED_TO** → [[intent-control-surface-builder]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]
