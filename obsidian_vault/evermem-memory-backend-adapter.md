---
id: "SKILL::evermem-memory-backend-adapter"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# evermem-memory-backend-adapter
**Node ID:** `SKILL::evermem-memory-backend-adapter`

## Description
Evermem memory backend adapter

## Properties
- **skill_type**: adapter
- **source_type**: operator_module
- **source_path**: system_v4/skills/evermem_adapter.py
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_high_intake_graph_v1", "a2_low_control_graph_v1"]
- **inputs**: ["content", "msg_id", "sender", "memory_types", "base_url", "timeout_seconds"]
- **outputs**: ["success", "msg_id", "status_code", "error"]
- **adapters**: {"shell": "system_v4/skills/evermem_adapter.py", "dispatch_binding": "python_module"}
- **related_skills**: ["witness-evermem-sync", "pimono-evermem-adapter"]

## Outward Relations
- **RELATED_TO** → [[witness-evermem-sync]]
- **RELATED_TO** → [[pimono-evermem-adapter]]
- **SKILL_OPERATES_ON** → [[a2_canonical_schemas]]
- **MEMBER_OF** → [[Outside Memory Control]]

## Inward Relations
- [[witness-evermem-sync]] → **RELATED_TO**
- [[pimono-evermem-adapter]] → **RELATED_TO**
- [[witness-memory-retriever]] → **RELATED_TO**
