---
id: "SKILL::skill-improver-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# skill-improver-operator
**Node ID:** `SKILL::skill-improver-operator`

## Description
Gated skill improvement operator

## Properties
- **skill_type**: operator
- **source_type**: operator_module
- **source_path**: system_v4/skills/skill_improver_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "a2_mid_refinement_graph_v1"]
- **inputs**: ["target_skill_path", "candidate_code", "test_command", "allow_write", "approval_token", "allowed_targets", "recorder"]
- **outputs**: ["improved", "detail", "path", "proposed_change", "compile_ok", "tests_state", "score", "write_permitted", "dry_run"]
- **adapters**: {"shell": "system_v4/skills/skill_improver_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["autoresearch-operator", "llm-council-operator", "a2-skill-improver-readiness-operator"]

## Outward Relations
- **RELATED_TO** → [[autoresearch-operator]]
- **RELATED_TO** → [[llm-council-operator]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]
- **MEMBER_OF** → [[Next State Signal Adaptation]]

## Inward Relations
- [[autoresearch-operator]] → **RELATED_TO**
- [[llm-council-operator]] → **RELATED_TO**
- [[a2-skill-source-intake-operator]] → **RELATED_TO**
- [[a2-tracked-work-operator]] → **RELATED_TO**
- [[a2-skill-improver-readiness-operator]] → **RELATED_TO**
- [[a2-skill-improver-target-selector-operator]] → **RELATED_TO**
- [[a2-skill-improver-dry-run-operator]] → **RELATED_TO**
- [[a2-skill-improver-first-target-proof-operator]] → **RELATED_TO**
- [[a2-skill-improver-second-target-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-improver-context-bridge-audit-operator]] → **RELATED_TO**
- [[a2-next-state-first-target-context-consumer-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-first-target-context-consumer-proof-operator]] → **RELATED_TO**
