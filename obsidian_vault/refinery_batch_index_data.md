---
id: "A2_3::SOURCE_MAP_PASS::refinery_batch_index_data::efc5944da63b68f5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# refinery_batch_index_data
**Node ID:** `A2_3::SOURCE_MAP_PASS::refinery_batch_index_data::efc5944da63b68f5`

## Description
Batch index (152KB). Records every batch created by the refinery: batch_id, layer, extraction_mode, doc path, node IDs, edge IDs. The complete lineage index for all ingested content.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[rosetta_translation_state]]
- **DEPENDS_ON** → [[index]]

## Inward Relations
- [[refinery_batch_index.json]] → **SOURCE_MAP_PASS**
- [[a2_persistent_brain_skill]] → **RELATED_TO**
- [[doc_queue_state]] → **RELATED_TO**
- [[persistent_memory_state]] → **RELATED_TO**
- [[a2_proposal_state]] → **RELATED_TO**
- [[a2_refinery_graph_data]] → **STRUCTURALLY_RELATED**
