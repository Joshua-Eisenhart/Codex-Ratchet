---
id: "SKILL::generate-doc-queue"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# generate-doc-queue
**Node ID:** `SKILL::generate-doc-queue`

## Description
Manage document processing queue

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/generate_doc_queue.py
- **status**: active
- **applicable_layers**: ["INDEX"]
- **applicable_trust_zones**: ["INDEX"]
- **applicable_graphs**: ["provenance"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/generate_doc_queue.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a1_queue_status_surface]]
