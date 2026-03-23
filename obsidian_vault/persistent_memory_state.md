---
id: "A2_3::SOURCE_MAP_PASS::persistent_memory_state::aa6cc5c9330bc4af"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# persistent_memory_state
**Node ID:** `A2_3::SOURCE_MAP_PASS::persistent_memory_state::aa6cc5c9330bc4af`

## Description
Persistent memory store (1KB JSONL). A2 brain memory entries for cross-session continuity.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[refinery_batch_index_data]]
- **RELATED_TO** → [[rosetta_translation_state]]
- **DEPENDS_ON** → [[session]]

## Inward Relations
- [[memory.jsonl]] → **SOURCE_MAP_PASS**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[doc_queue_state]] → **RELATED_TO**
- [[a2_proposal_state]] → **RELATED_TO**
