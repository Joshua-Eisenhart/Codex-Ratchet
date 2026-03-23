---
id: "A2_3::SOURCE_MAP_PASS::refinery_session_log_corpus::6c4932d5e0a1e5fb"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# refinery_session_log_corpus
**Node ID:** `A2_3::SOURCE_MAP_PASS::refinery_session_log_corpus::6c4932d5e0a1e5fb`

## Description
27 session logs documenting every refinery execution. Sessions include: mass extraction waves 4-14, spec/supplement/upgrade/control_plane/a2_state/final waves, Opus audit, patch verification, promotion audit, contradiction scan, reference ingest, self-referential ingest, thread context ingest. Each log records: session ID, start/end time, docs processed, batches created, nodes/edges added, findings. The complete execution trail of the refinery itself.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[system_reboot_protocol]]
- **RELATED_TO** → [[thread_context_v3_reboot_doc]]
- **DEPENDS_ON** → [[start]]
- **DEPENDS_ON** → [[reference]]
- **DEPENDS_ON** → [[session]]

## Inward Relations
- [[MASS_UPGRADE_DOCS_WAVE_11_SESSION.md]] → **SOURCE_MAP_PASS**
