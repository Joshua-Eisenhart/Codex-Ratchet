---
id: "SKILL::a2-source-family-lane-selector-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-source-family-lane-selector-operator
**Node ID:** `SKILL::a2-source-family-lane-selector-operator`

## Description
Audit-only selector that recommends the next bounded non-lev source-family lane from current corpus and hold state

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_source_family_lane_selector_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_source_family_lane_selection_report", "a2_source_family_lane_selection_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-source-family-lane-selector-operator/SKILL.md", "shell": "system_v4/skills/a2_source_family_lane_selector_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-skill-source-intake-operator", "a2-research-deliberation-operator", "a2-lev-agents-promotion-operator"]

## Outward Relations
- **RELATED_TO** → [[a2-skill-source-intake-operator]]
- **RELATED_TO** → [[a2-research-deliberation-operator]]
- **RELATED_TO** → [[a2-lev-agents-promotion-operator]]

## Inward Relations
- [[a2-context-spec-workflow-pattern-audit-operator]] → **RELATED_TO**
- [[a2-autoresearch-council-runtime-proof-operator]] → **RELATED_TO**
- [[a2-context-spec-workflow-follow-on-selector-operator]] → **RELATED_TO**
