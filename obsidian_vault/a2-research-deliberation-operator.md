---
id: "SKILL::a2-research-deliberation-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-research-deliberation-operator
**Node ID:** `SKILL::a2-research-deliberation-operator`

## Description
A2 research deliberation cluster operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_research_deliberation_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "B_ADJUDICATED"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "B_ADJUDICATED"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["question", "state", "generator", "evaluator", "candidates", "report_path"]
- **outputs**: ["deliberation_report"]
- **adapters**: {"shell": "system_v4/skills/a2_research_deliberation_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["autoresearch-operator", "llm-council-operator", "a2-tracked-work-operator"]

## Outward Relations
- **RELATED_TO** → [[autoresearch-operator]]
- **RELATED_TO** → [[llm-council-operator]]
- **RELATED_TO** → [[a2-tracked-work-operator]]

## Inward Relations
- [[a2-source-family-lane-selector-operator]] → **RELATED_TO**
- [[a2-context-spec-workflow-pattern-audit-operator]] → **RELATED_TO**
- [[a2-autoresearch-council-runtime-proof-operator]] → **RELATED_TO**
