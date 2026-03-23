---
id: "SKILL::a2-workshop-analysis-gate-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-workshop-analysis-gate-operator
**Node ID:** `SKILL::a2-workshop-analysis-gate-operator`

## Description
A2 workshop analysis gate operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_workshop_analysis_gate_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "candidate", "candidate_path", "intake_context_path", "source_refs", "report_path", "markdown_path", "packet_path"]
- **outputs**: ["workshop_analysis_gate_report", "workshop_analysis_gate_packet"]
- **adapters**: {"shell": "system_v4/skills/a2_workshop_analysis_gate_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-skill-source-intake-operator", "a2-tracked-work-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-skill-source-intake-operator]]
- **RELATED_TO** → [[a2-tracked-work-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]

## Inward Relations
- [[outer-session-ledger]] → **RELATED_TO**
- [[outside-control-shell-operator]] → **RELATED_TO**
- [[a2-lev-agents-promotion-operator]] → **RELATED_TO**
- [[a2-lev-builder-placement-audit-operator]] → **RELATED_TO**
