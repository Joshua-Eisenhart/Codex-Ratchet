---
id: "A2_3::SOURCE_MAP_PASS::system_reboot_protocol::5bb3fa3cace0a2ee"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# system_reboot_protocol
**Node ID:** `A2_3::SOURCE_MAP_PASS::system_reboot_protocol::5bb3fa3cace0a2ee`

## Description
Reboot protocol: (1) read THREAD_CONTEXT_EXTRACT v3, (2) load graph from system_v4/a2_state/graphs/system_graph_a2_refinery.json, (3) run graph_audit() to verify CLEAN, (4) check doc_queue status, (5) resume from pending actions list. The thread context extract IS the continuity mechanism — each session writes an updated version. The system knows itself through self-referential ingestion.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[thread_context_v3_reboot_doc]]
- **DEPENDS_ON** → [[verify]]
- **DEPENDS_ON** → [[session]]

## Inward Relations
- [[THREAD_CONTEXT_EXTRACT__ANTIGRAVITY__2026_03_18__v3.md]] → **SOURCE_MAP_PASS**
- [[refinery_session_log_corpus]] → **RELATED_TO**
- [[live_thread_context_reboot_key]] → **RELATED_TO**
