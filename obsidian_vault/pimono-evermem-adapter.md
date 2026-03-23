---
id: "SKILL::pimono-evermem-adapter"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# pimono-evermem-adapter
**Node ID:** `SKILL::pimono-evermem-adapter`

## Description
Pimono Evermem adapter

## Properties
- **skill_type**: adapter
- **source_type**: operator_module
- **source_path**: system_v4/skills/pimono_evermem_adapter.py
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_high_intake_graph_v1"]
- **inputs**: ["query", "user_id", "limit"]
- **outputs**: ["context_blocks", "count", "status"]
- **adapters**: {"shell": "system_v4/skills/pimono_evermem_adapter.py", "dispatch_binding": "python_module"}
- **related_skills**: ["evermem-memory-backend-adapter", "witness-evermem-sync"]

## Outward Relations
- **RELATED_TO** → [[evermem-memory-backend-adapter]]
- **RELATED_TO** → [[witness-evermem-sync]]
- **SKILL_OPERATES_ON** → [[a2_canonical_schemas]]
- **MEMBER_OF** → [[Outside Memory Control]]

## Inward Relations
- [[evermem-memory-backend-adapter]] → **RELATED_TO**
- [[witness-evermem-sync]] → **RELATED_TO**
