---
id: "SKILL::graveyard-router"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# graveyard-router
**Node ID:** `SKILL::graveyard-router`

## Description
Route failures to graveyard + attractor memory

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/graveyard_router.py
- **status**: active
- **applicable_layers**: ["GRAVEYARD"]
- **applicable_trust_zones**: ["GRAVEYARD"]
- **applicable_graphs**: ["graveyard"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/graveyard_router.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[elimination_over_truth]]
