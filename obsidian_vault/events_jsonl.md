---
id: "A2_3::SOURCE_MAP_PASS::events_jsonl::64e1e256fb633f0a"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# events_jsonl
**Node ID:** `A2_3::SOURCE_MAP_PASS::events_jsonl::64e1e256fb633f0a`

## Description
Unprocessed File Type (events.jsonl): {"a0_to_a1_save_zip_relpath":"zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip","event":"a1_strategy_request_emitted","last_reject_tags":[],"source":"ZIP_PROTOCOL_v2","state_hash":"195f26af605cac551eab421572798f4c268bf1bb91115e0f545784b4ed3b0b42","step":1} |

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 5 sources, 4 batches, 6 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **RELATED_TO** → [[kernel_py]]
- **DEPENDS_ON** → [[ZIP_PROTOCOL_V2]]
- **DEPENDS_ON** → [[events]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[request]]

## Inward Relations
- [[events.000.jsonl]] → **SOURCE_MAP_PASS**
- [[events.000.jsonl]] → **OVERLAPS**
- [[events.000.jsonl]] → **OVERLAPS**
- [[events.000.jsonl]] → **OVERLAPS**
- [[events.000.jsonl]] → **OVERLAPS**
