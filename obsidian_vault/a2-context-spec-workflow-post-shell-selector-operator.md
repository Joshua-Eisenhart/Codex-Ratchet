---
id: "SKILL::a2-context-spec-workflow-post-shell-selector-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-context-spec-workflow-post-shell-selector-operator
**Node ID:** `SKILL::a2-context-spec-workflow-post-shell-selector-operator`

## Description
Selector-only post-shell controller slice for the context-spec-workflow-memory cluster that holds the lane after append-safe landing and records the first standby follow-on without widening by momentum

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_context_spec_workflow_post_shell_selector_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "selection_scope", "append_safe_report_path", "follow_on_selector_report_path", "evermem_report_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_context_spec_workflow_post_shell_selector_report", "a2_context_spec_workflow_post_shell_selector_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-context-spec-workflow-post-shell-selector-operator/SKILL.md", "shell": "system_v4/skills/a2_context_spec_workflow_post_shell_selector_operator.py", "dispatch_bindin
- **related_skills**: ["a2-append-safe-context-shell-audit-operator", "a2-context-spec-workflow-follow-on-selector-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-append-safe-context-shell-audit-operator]]
- **RELATED_TO** → [[a2-context-spec-workflow-follow-on-selector-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
