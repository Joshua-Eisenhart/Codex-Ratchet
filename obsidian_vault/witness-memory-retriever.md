---
id: "SKILL::witness-memory-retriever"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# witness-memory-retriever
**Node ID:** `SKILL::witness-memory-retriever`

## Description
Bounded EverMem witness-memory retrieval probe that attempts one witness-derived lookup and emits repo-held report surfaces without claiming bootstrap or broader memory integration

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/witness_memory_retriever.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "B_ADJUDICATED"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "B_ADJUDICATED"]
- **applicable_graphs**: ["runtime", "control", "a2_low_control_graph_v1"]
- **inputs**: ["repo_root", "witness_path", "sync_report_path", "query", "evermem_url", "timeout_seconds", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["witness_memory_retriever_report", "witness_memory_retriever_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/witness-memory-retriever/SKILL.md", "shell": "system_v4/skills/witness_memory_retriever.py", "dispatch_binding": "python_module"}
- **related_skills**: ["witness-evermem-sync", "evermem-memory-backend-adapter", "outside-control-shell-operator"]

## Outward Relations
- **RELATED_TO** → [[witness-evermem-sync]]
- **RELATED_TO** → [[evermem-memory-backend-adapter]]
- **RELATED_TO** → [[outside-control-shell-operator]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]

## Inward Relations
- [[a2-evermem-backend-reachability-audit-operator]] → **RELATED_TO**
