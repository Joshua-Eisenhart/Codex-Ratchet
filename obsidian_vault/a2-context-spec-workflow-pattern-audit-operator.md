---
id: "SKILL::a2-context-spec-workflow-pattern-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-context-spec-workflow-pattern-audit-operator
**Node ID:** `SKILL::a2-context-spec-workflow-pattern-audit-operator`

## Description
Audit-only first slice for the context-spec-workflow-memory cluster that maps append-safe context, executable spec coupling, workflow discipline, and scoped memory-sidecar patterns onto current Ratchet seams

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_context_spec_workflow_pattern_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "analysis_scope", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_context_spec_workflow_pattern_audit_report", "a2_context_spec_workflow_pattern_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-context-spec-workflow-pattern-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_context_spec_workflow_pattern_audit_operator.py", "dispatch_binding": "python_
- **related_skills**: ["a2-source-family-lane-selector-operator", "a2-skill-source-intake-operator", "a2-research-deliberation-operator"]

## Outward Relations
- **RELATED_TO** → [[a2-source-family-lane-selector-operator]]
- **RELATED_TO** → [[a2-skill-source-intake-operator]]
- **RELATED_TO** → [[a2-research-deliberation-operator]]

## Inward Relations
- [[a2-context-spec-workflow-follow-on-selector-operator]] → **RELATED_TO**
- [[a2-append-safe-context-shell-audit-operator]] → **RELATED_TO**
