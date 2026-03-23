---
id: "A2_3::SOURCE_MAP_PASS::packet_journal_compaction_rules::5b6aa939e593f7d9"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# packet_journal_compaction_rules
**Node ID:** `A2_3::SOURCE_MAP_PASS::packet_journal_compaction_rules::5b6aa939e593f7d9`

## Description
Compaction is class-specific: checkpoint classes (B_TO_A0_STATE_UPDATE_ZIP, A0_TO_A1_SAVE_ZIP) retain earliest/latest/sparse/recent-tail. Strategy history is more conservative. SIM results should not be aggressively compacted. EXPORT_BATCH is lowest priority to compact.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[regeneration_witness_retention]]

## Inward Relations
- [[16_ZIP_SAVE_AND_TAPES_SPEC.md]] → **SOURCE_MAP_PASS**
- [[entropy_compaction_contract]] → **RELATED_TO**
