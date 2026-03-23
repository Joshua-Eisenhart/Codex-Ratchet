---
id: "SKILL::a2-append-safe-context-shell-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-append-safe-context-shell-audit-operator
**Node ID:** `SKILL::a2-append-safe-context-shell-audit-operator`

## Description
Audit-only append-safe context-shell slice for the context-spec-workflow-memory cluster that maps current standing A2 continuity surfaces, admitted write shapes, and anti-bloat fences

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_append_safe_context_shell_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "audit_scope", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_append_safe_context_shell_audit_report", "a2_append_safe_context_shell_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-append-safe-context-shell-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_append_safe_context_shell_audit_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-context-spec-workflow-follow-on-selector-operator", "a2-context-spec-workflow-pattern-audit-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-context-spec-workflow-follow-on-selector-operator]]
- **RELATED_TO** → [[a2-context-spec-workflow-pattern-audit-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]

## Inward Relations
- [[a2-context-spec-workflow-post-shell-selector-operator]] → **RELATED_TO**
