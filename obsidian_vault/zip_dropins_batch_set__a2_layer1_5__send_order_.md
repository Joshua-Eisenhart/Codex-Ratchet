---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_batch_set__a2_layer1_5__send_order_::9d93d2b76eef90dd"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "NONCANON"
---

# zip_dropins_batch_set__a2_layer1_5__send_order_
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_batch_set__a2_layer1_5__send_order_::9d93d2b76eef90dd`

## Description
BATCH_SET__A2_LAYER1_5__SEND_ORDER__STAGE3_PRO_RUN__v1.md (2002B): # Stage-3 Pro Send Order (Single Attachment)  - Attach exactly one batch zip per fresh thread. - Send text: `run this zip job and return only output zip.` - Keep batch ids and output names unchanged.  ## BATCH_01_OF_10 - Input zip: `BATCH_01_OF_10__A

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 7 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[input]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[send_text]]
- **DEPENDS_ON** → [[batch_set__a2_layer1_5__send_order__stage3_pro_run]]

## Inward Relations
- [[BATCH_SET__A2_LAYER1_5__SEND_ORDER__STAGE3_PRO_RUN__v1.md]] → **SOURCE_MAP_PASS**
- [[ROSETTA_IGT_ENGINE_STRATEGY_PATTERN_TABLES.out.md]] → **OVERLAPS**
- [[batch_set__a2_layer1_5__send_order__stage3_pro_run]] → **STRUCTURALLY_RELATED**
