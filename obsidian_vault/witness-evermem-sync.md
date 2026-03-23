---
id: "SKILL::witness-evermem-sync"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# witness-evermem-sync
**Node ID:** `SKILL::witness-evermem-sync`

## Description
Witness Evermem sync adapter

## Properties
- **skill_type**: adapter
- **source_type**: operator_module
- **source_path**: system_v4/skills/witness_evermem_sync.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "B_ADJUDICATED"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "B_ADJUDICATED"]
- **applicable_graphs**: ["runtime", "control", "a2_low_control_graph_v1"]
- **inputs**: ["witness_path", "last_sync_idx", "evermem_url", "state_path", "report_json_path", "report_md_path", "timeout_seconds"]
- **outputs**: ["previous_idx", "new_idx", "synced", "attempted_count", "remaining_count", "status", "first_error", "state_path", "report_json_path", "report_md_path"]
- **adapters**: {"shell": "system_v4/skills/witness_evermem_sync.py", "dispatch_binding": "python_module"}
- **related_skills**: ["evermem-memory-backend-adapter", "pimono-evermem-adapter"]

## Outward Relations
- **RELATED_TO** → [[evermem-memory-backend-adapter]]
- **RELATED_TO** → [[pimono-evermem-adapter]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]
- **MEMBER_OF** → [[Outside Memory Control]]

## Inward Relations
- [[evermem-memory-backend-adapter]] → **RELATED_TO**
- [[pimono-evermem-adapter]] → **RELATED_TO**
- [[a2-skill-source-intake-operator]] → **RELATED_TO**
- [[outer-session-ledger]] → **RELATED_TO**
- [[witness-memory-retriever]] → **RELATED_TO**
- [[a2-evermem-backend-reachability-audit-operator]] → **RELATED_TO**
