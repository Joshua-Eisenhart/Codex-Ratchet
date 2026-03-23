---
id: "SKILL::b-adjudicator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# b-adjudicator
**Node ID:** `SKILL::b-adjudicator`

## Description
Bridge: runs B adjudication on graph nodes

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/b_adjudicator.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED"]
- **applicable_trust_zones**: ["B_ADJUDICATED"]
- **applicable_graphs**: ["runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/b_adjudicator.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[b_kernel_7_stage_pipeline]]
- **SKILL_OPERATES_ON** → [[b_canon_state_objects]]
