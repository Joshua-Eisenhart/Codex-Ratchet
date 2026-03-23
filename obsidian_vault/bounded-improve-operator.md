---
id: "SKILL::bounded-improve-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# bounded-improve-operator
**Node ID:** `SKILL::bounded-improve-operator`

## Description
Bounded Improve Operator

## Properties
- **skill_type**: refinement
- **source_type**: python_module
- **source_path**: system_v4/skills/bounded_improve_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT"]
- **applicable_graphs**: ["a2_mid_refinement_graph_v1"]
- **inputs**: ["runtime_state", "mutation_fn", "eval_fn"]
- **outputs**: ["improved_state", "improvement_result"]
- **adapters**: {"shell": "system_v4/skills/bounded_improve_operator.py"}
- **related_skills**: []

## Outward Relations
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]

## Inward Relations
- [[intent-control-surface-builder]] → **RELATED_TO**
- [[autoresearch-operator]] → **RELATED_TO**
- [[llm-council-operator]] → **RELATED_TO**
- [[a2-next-state-signal-adaptation-audit-operator]] → **RELATED_TO**
