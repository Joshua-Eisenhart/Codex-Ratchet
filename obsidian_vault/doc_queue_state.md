---
id: "A2_3::SOURCE_MAP_PASS::doc_queue_state::a9a71386ec152f42"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# doc_queue_state
**Node ID:** `A2_3::SOURCE_MAP_PASS::doc_queue_state::a9a71386ec152f42`

## Description
Document queue (227KB). 893 entries tracking every file in the workspace. Fields: path, entropy_class, status (DONE/PENDING), size_bytes, file_type, processed_batch_id. Sorted by entropy class order. The intake manifest for the refinery.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[refinery_batch_index_data]]
- **RELATED_TO** → [[rosetta_translation_state]]
- **RELATED_TO** → [[persistent_memory_state]]
- **RELATED_TO** → [[slice_compiler_skill_family]]

## Inward Relations
- [[doc_queue.json]] → **SOURCE_MAP_PASS**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[a2_proposal_state]] → **RELATED_TO**
- [[doc_queue_generator_skill]] → **RELATED_TO**
