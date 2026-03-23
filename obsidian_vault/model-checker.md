---
id: "SKILL::model-checker"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# model-checker
**Node ID:** `SKILL::model-checker`

## Description
Model Checker

## Properties
- **skill_type**: verification
- **source_type**: python_module
- **source_path**: system_v4/skills/model_checker.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED"]
- **applicable_trust_zones**: ["B_ADJUDICATED"]
- **applicable_graphs**: []
- **inputs**: ["runtime_state", "transforms"]
- **outputs**: ["exploration_result", "counterexamples"]
- **adapters**: {"shell": "system_v4/skills/model_checker.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[constraint_ladder_contracts]]
