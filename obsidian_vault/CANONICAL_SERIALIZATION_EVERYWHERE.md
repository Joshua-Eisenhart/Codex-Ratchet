---
id: "A2_3::ENGINE_PATTERN_PASS::CANONICAL_SERIALIZATION_EVERYWHERE::fb99dc0ad0f80651"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# CANONICAL_SERIALIZATION_EVERYWHERE
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::CANONICAL_SERIALIZATION_EVERYWHERE::fb99dc0ad0f80651`

## Description
All JSON files use json.dumps(sort_keys=True, separators=(',',':')) with trailing newline. All text files enforce no-CR, no-trailing-spaces, trailing-LF. ZIP timestamps are fixed to (1980,1,1,0,0,0). This makes every byte deterministic and hashable.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[zip_protocol_v2_contract]]
- **RELATED_TO** → [[sim_deterministic_replay]]
- **RELATED_TO** → [[SIM_Deterministic_Hashing]]
- **RELATED_TO** → [[DETERMINISTIC_REPLAY_HASH_EQUALITY]]

## Inward Relations
- [[zip_protocol_v2_validator.py]] → **ENGINE_PATTERN_PASS**
