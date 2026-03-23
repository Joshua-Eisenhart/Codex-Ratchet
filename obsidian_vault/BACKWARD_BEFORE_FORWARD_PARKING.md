---
id: "A2_3::ENGINE_PATTERN_PASS::BACKWARD_BEFORE_FORWARD_PARKING::f38f7974fbef0b5c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# BACKWARD_BEFORE_FORWARD_PARKING
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::BACKWARD_BEFORE_FORWARD_PARKING::f38f7974fbef0b5c`

## Description
A backward ZIP (B_TO_A0) arriving before any forward ZIP (A1_TO_A0 or A0_TO_B) for the same run_id is PARKED, not rejected. Once forward arrives, backward can proceed. Sequence regression (replaying an already-accepted sequence) is hard REJECTED.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[SEQUENCE_MONOTONICITY_WITH_PARK]]

## Inward Relations
- [[test_zip_protocol_v2_validator.py]] → **ENGINE_PATTERN_PASS**
