---
id: "SKILL::llm-council-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# llm-council-operator
**Node ID:** `SKILL::llm-council-operator`

## Description
LLM council adjudication operator

## Properties
- **skill_type**: adjudicator
- **source_type**: operator_module
- **source_path**: system_v4/skills/llm_council_operator.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["B_ADJUDICATED", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "a2_low_control_graph_v1"]
- **inputs**: ["candidates", "consensus_threshold"]
- **outputs**: ["accepted", "rejected", "proceedings"]
- **adapters**: {"shell": "system_v4/skills/llm_council_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["autoresearch-operator", "bounded-improve-operator", "skill-improver-operator"]

## Outward Relations
- **RELATED_TO** → [[autoresearch-operator]]
- **RELATED_TO** → [[bounded-improve-operator]]
- **RELATED_TO** → [[skill-improver-operator]]
- **SKILL_OPERATES_ON** → [[karpathy_autoresearch_cegis_loop]]

## Inward Relations
- [[autoresearch-operator]] → **RELATED_TO**
- [[skill-improver-operator]] → **RELATED_TO**
- [[a2-research-deliberation-operator]] → **RELATED_TO**
- [[a2-autoresearch-council-runtime-proof-operator]] → **RELATED_TO**
