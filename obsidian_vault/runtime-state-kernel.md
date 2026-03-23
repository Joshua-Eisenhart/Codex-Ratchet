---
id: "SKILL::runtime-state-kernel"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# runtime-state-kernel
**Node ID:** `SKILL::runtime-state-kernel`

## Description
Runtime State Kernel

## Properties
- **skill_type**: bridge
- **source_type**: python_module
- **source_path**: system_v4/skills/runtime_state_kernel.py
- **status**: active
- **applicable_layers**: ["INDEX"]
- **applicable_trust_zones**: ["INDEX"]
- **applicable_graphs**: ["identity_registry_v1"]
- **inputs**: []
- **outputs**: ["runtime_state", "probe", "transform", "witness"]
- **adapters**: {"shell": "system_v4/skills/runtime_state_kernel.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[kernel_seed_state]]

## Inward Relations
- [[a2-next-state-signal-adaptation-audit-operator]] → **RELATED_TO**
- [[a2-next-state-directive-signal-probe-operator]] → **RELATED_TO**
