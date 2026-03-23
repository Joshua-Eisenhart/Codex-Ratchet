---
id: "A2_3::ENGINE_PATTERN_PASS::ZIP_PROTOCOL_V2_EIGHT_TYPE_SYSTEM::c62411f07f737ab3"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# ZIP_PROTOCOL_V2_EIGHT_TYPE_SYSTEM
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::ZIP_PROTOCOL_V2_EIGHT_TYPE_SYSTEM::c62411f07f737ab3`

## Description
8 ZIP types define the full communication topology: A2_TO_A1_PROPOSAL_ZIP, A1_TO_A0_STRATEGY_ZIP, A0_TO_B_EXPORT_BATCH_ZIP (FORWARD) + B_TO_A0_STATE_UPDATE_ZIP, SIM_TO_A0_SIM_RESULT_ZIP, A0_TO_A1_SAVE_ZIP, A1_TO_A2_SAVE_ZIP, A2_META_SAVE_ZIP (BACKWARD). Each type has fixed source/target layers and allowed payload files.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[end_to_end_loop]]

## Inward Relations
- [[zip_protocol_v2_validator.py]] → **ENGINE_PATTERN_PASS**
- [[V4_Pipeline_Components_Exist]] → **RELATED_TO**
- [[FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM]] → **RELATED_TO**
