---
id: "SKILL::a2-context-spec-workflow-follow-on-selector-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-context-spec-workflow-follow-on-selector-operator
**Node ID:** `SKILL::a2-context-spec-workflow-follow-on-selector-operator`

## Description
Selector-only follow-on operator that chooses one bounded second slice for the context-spec-workflow-memory cluster without widening into runtime, service, or substrate claims

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_context_spec_workflow_follow_on_selector_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "selection_scope", "pattern_report_path", "pattern_packet_path", "source_selector_report_path", "evermem_report_path", "controller_record_path", "report_json_path", "report_md_path", "pa
- **outputs**: ["a2_context_spec_workflow_follow_on_selector_report", "a2_context_spec_workflow_follow_on_selector_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-context-spec-workflow-follow-on-selector-operator/SKILL.md", "shell": "system_v4/skills/a2_context_spec_workflow_follow_on_selector_operator.py", "dispatch_binding"
- **related_skills**: ["a2-context-spec-workflow-pattern-audit-operator", "a2-source-family-lane-selector-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-context-spec-workflow-pattern-audit-operator]]
- **RELATED_TO** → [[a2-source-family-lane-selector-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]

## Inward Relations
- [[a2-append-safe-context-shell-audit-operator]] → **RELATED_TO**
- [[a2-context-spec-workflow-post-shell-selector-operator]] → **RELATED_TO**
