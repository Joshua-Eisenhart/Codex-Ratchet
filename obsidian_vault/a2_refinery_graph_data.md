---
id: "A2_3::SOURCE_MAP_PASS::a2_refinery_graph_data::bef8b98ee0bcf040"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# a2_refinery_graph_data
**Node ID:** `A2_3::SOURCE_MAP_PASS::a2_refinery_graph_data::bef8b98ee0bcf040`

## Description
The A2 refinery graph JSON (563KB). Contains all 394+ nodes and 299+ edges. Node structure: id, node_type (SOURCE_DOCUMENT/EXTRACTED_CONCEPT/REFINED_CONCEPT/KERNEL_CONCEPT), layer, trust_zone (A2_3_INTAKE/A2_2_CANDIDATE/A2_1_KERNEL), admissibility_state, properties, lineage_refs, witness_refs. Edge structure: source_id, target_id, relation, attributes.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[v3_ingest_graph_data]]
- **STRUCTURALLY_RELATED** → [[refinery_batch_index_data]]

## Inward Relations
- [[system_graph_a2_refinery.json]] → **SOURCE_MAP_PASS**
- [[a2_graph_refinery_skill]] → **RELATED_TO**
