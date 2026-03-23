---
id: "SKILL::b-kernel"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# b-kernel
**Node ID:** `SKILL::b-kernel`

## Description
B-kernel adjudication (accept/park/reject)

## Properties
- **skill_type**: verification
- **source_type**: operator_module
- **source_path**: system_v4/skills/b_kernel.py
- **status**: active
- **applicable_layers**: ["B_ADJUDICATED"]
- **applicable_trust_zones**: ["B_ADJUDICATED"]
- **applicable_graphs**: ["runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/b_kernel.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[b_kernel_7_stage_pipeline]]
- **SKILL_OPERATES_ON** → [[b_canon_state_objects]]
- **SKILL_OPERATES_ON** → [[DETERMINISTIC_KERNEL_PIPELINE]]
- **SKILL_OPERATES_ON** → [[derived_only_guard]]
- **SKILL_OPERATES_ON** → [[elimination_over_truth]]

## Inward Relations
- [[graveyard-lawyer]] → **RELATED_TO**
- [[GRAVEYARD_F024]] → **RELATED_TO**
- [[GRAVEYARD_F048]] → **RELATED_TO**
