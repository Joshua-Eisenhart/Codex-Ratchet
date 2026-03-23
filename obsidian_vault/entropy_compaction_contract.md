---
id: "A2_3::SOURCE_MAP_PASS::entropy_compaction_contract::f13ae8d966bb503c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# entropy_compaction_contract
**Node ID:** `A2_3::SOURCE_MAP_PASS::entropy_compaction_contract::f13ae8d966bb503c`

## Description
Compaction reduces high-entropy memory entries to low-entropy summaries (INTENT_SUMMARY.md, MODEL_CONTEXT.md). Each compaction writes an A2_MEMORY_ENTRY_v1 with entry_type=COMPACTION_EVENT, derived_from_entry_ids[], and output_hashes[]. Source entries remain immutable.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[packet_journal_compaction_rules]]

## Inward Relations
- [[19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md]] → **SOURCE_MAP_PASS**
- [[entropy_compaction]] → **RELATED_TO**
