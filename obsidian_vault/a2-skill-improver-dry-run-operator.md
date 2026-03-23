---
id: "SKILL::a2-skill-improver-dry-run-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-skill-improver-dry-run-operator
**Node ID:** `SKILL::a2-skill-improver-dry-run-operator`

## Description
Bounded dry-run first-target bridge over skill-improver-operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_skill_improver_dry_run_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["target_skill_id", "candidate_code", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["status", "selected_target", "improver_result", "report_json_path", "report_md_path", "packet_path"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-skill-improver-dry-run-operator/SKILL.md", "shell": "system_v4/skills/a2_skill_improver_dry_run_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["skill-improver-operator", "a2-skill-improver-readiness-operator", "a2-skill-improver-target-selector-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **RELATED_TO** → [[a2-skill-improver-target-selector-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]

## Inward Relations
- [[a2-skill-improver-first-target-proof-operator]] → **RELATED_TO**
