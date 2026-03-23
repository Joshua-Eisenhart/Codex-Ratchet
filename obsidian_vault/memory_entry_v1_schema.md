---
id: "A2_3::SOURCE_MAP_PASS::memory_entry_v1_schema::a157d9b21b6ce842"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# memory_entry_v1_schema
**Node ID:** `A2_3::SOURCE_MAP_PASS::memory_entry_v1_schema::a157d9b21b6ce842`

## Description
A2_MEMORY_ENTRY_v1 in memory.jsonl: required keys are schema, entry_id (monotonic), ts_utc, entry_type, content, source_refs[] (path+sha256 pairs), tags[]. Optional: run_id, state_hash, derived_from_entry_ids[]. Append-only, sharded at 65536 bytes or 2000 lines.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md]] → **SOURCE_MAP_PASS**
- [[a1_kernel_lane_item_object]] → **RELATED_TO**
