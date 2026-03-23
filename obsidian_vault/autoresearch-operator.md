---
id: "SKILL::autoresearch-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# autoresearch-operator
**Node ID:** `SKILL::autoresearch-operator`

## Description
Autoresearch operator

## Properties
- **skill_type**: agent
- **source_type**: operator_module
- **source_path**: system_v4/skills/autoresearch_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "a2_mid_refinement_graph_v1"]
- **inputs**: ["state", "generator", "evaluator"]
- **outputs**: ["best_state", "stats"]
- **adapters**: {"shell": "system_v4/skills/autoresearch_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["bounded-improve-operator", "llm-council-operator", "skill-improver-operator"]

## Outward Relations
- **RELATED_TO** → [[bounded-improve-operator]]
- **RELATED_TO** → [[llm-council-operator]]
- **RELATED_TO** → [[skill-improver-operator]]
- **SKILL_OPERATES_ON** → [[karpathy_autoresearch_cegis_loop]]

## Inward Relations
- [[llm-council-operator]] → **RELATED_TO**
- [[skill-improver-operator]] → **RELATED_TO**
- [[a2-skill-source-intake-operator]] → **RELATED_TO**
- [[a2-research-deliberation-operator]] → **RELATED_TO**
- [[a2-autoresearch-council-runtime-proof-operator]] → **RELATED_TO**
